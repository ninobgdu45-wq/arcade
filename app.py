#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
Borne ARCADE du collège — version 6.0 (interface web complète)

Python (Flask) fait tourner un petit serveur local qui sert une interface
web néon/sobre. Le navigateur en mode kiosque affiche cette interface,
qui communique avec Python via une API JSON pour :
  - lister/lancer/déposer/supprimer des jeux, favoris, recherche
  - gérer les élèves et l'attribution des jeux (auteurs)
  - enregistrer des scores et afficher un classement (leaderboard)
  - détecter les manettes USB branchées
  - lire les infos système
  - administration : mot de passe, reboot, extinction, journal,
    sauvegarde/restauration de toutes les données

Lancement :
    python3 app.py
Puis ouvrir http://localhost:5000 dans le navigateur (idéalement en kiosque
avec chromium-browser --kiosk http://localhost:5000).
"""

import os
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file

import config
import jeux
import systeme
import admin
import eleves
import manettes
import scores

app = Flask(__name__)


def corps_json():
    """Récupère le JSON de la requête sans jamais lever d'exception."""
    try:
        return request.get_json(silent=True) or {}
    except Exception:
        return {}


@app.errorhandler(Exception)
def gerer_erreur_inattendue(erreur):
    import traceback
    traceback.print_exc()
    if request.path.startswith("/api/"):
        return jsonify({"succes": False, "message": f"Erreur serveur : {erreur}"}), 500
    return (
        f"<body style='background:#0a0b10;color:#e8eaf2;font-family:sans-serif;"
        f"padding:40px;'><h2>Erreur serveur</h2><p>{erreur}</p>"
        f"<p style='color:#7d8296'>Détail dans la console où tourne <code>app.py</code>.</p>"
        f"<a href='/' style='color:#2de2e6'>← Retour à l'accueil</a></body>",
        500,
    )


# ============================================================
#  Pages (rendu HTML)
# ============================================================
@app.route("/")
def page_accueil():
    return render_template("accueil.html")


@app.route("/bibliotheque")
def page_bibliotheque():
    return render_template("bibliotheque.html")


@app.route("/systeme")
def page_systeme():
    return render_template("systeme.html")


@app.route("/admin")
def page_admin():
    return render_template("admin.html")


@app.route("/eleves")
def page_eleves():
    return render_template("eleves.html")


@app.route("/classement")
def page_classement():
    return render_template("classement.html")


@app.route("/creer")
def page_creer():
    return render_template("creer.html")


# Permet d'afficher logo.png / droitsCC.png stockés dans ASSETS_DIR
@app.route("/assets/<nom_fichier>")
def servir_asset(nom_fichier):
    chemin_complet = os.path.join(config.ASSETS_DIR, nom_fichier)
    if not os.path.isfile(chemin_complet):
        return "", 404
    return send_from_directory(config.ASSETS_DIR, nom_fichier)


# Permet de jouer la musique d'ambiance déposée dans MUSIQUE_DIR
@app.route("/musique/<nom_fichier>")
def servir_musique(nom_fichier):
    chemin_complet = os.path.join(config.MUSIQUE_DIR, nom_fichier)
    if not os.path.isfile(chemin_complet):
        return "", 404
    return send_from_directory(config.MUSIQUE_DIR, nom_fichier)


@app.route("/api/musique/liste")
def api_liste_musique():
    if not os.path.isdir(config.MUSIQUE_DIR):
        return jsonify([])
    pistes = [f for f in os.listdir(config.MUSIQUE_DIR) if f.lower().endswith((".mp3", ".ogg", ".wav"))]
    return jsonify(sorted(pistes))


# ============================================================
#  API — Jeux
# ============================================================
@app.route("/api/jeux")
def api_lister_jeux():
    filtre = request.args.get("q", "")
    return jsonify(jeux.lister_tous_les_jeux(filtre))


@app.route("/api/jeux/lancer", methods=["POST"])
def api_lancer_jeu():
    nom = corps_json().get("nom", "")
    succes, message = jeux.lancer_jeu(nom, callback_log=admin.journaliser_lancement_jeu)
    return jsonify({"succes": succes, "message": message})


@app.route("/api/scratch/ouvrir", methods=["POST"])
def api_ouvrir_scratch():
    """Ouvre Scratch sans projet précis (raccourci clavier S)."""
    import subprocess
    try:
        subprocess.Popen(["scratch2"])
        admin.journaliser("ouverture_scratch_vide")
        return jsonify({"succes": True, "message": "Ouverture de Scratch…"})
    except FileNotFoundError:
        return jsonify({"succes": False, "message": "Scratch n'est pas installé sur cette borne."})
    except OSError as erreur:
        return jsonify({"succes": False, "message": f"Erreur : {erreur}"})


@app.route("/api/jeux/favori", methods=["POST"])
def api_favori_jeu():
    nom = corps_json().get("nom", "")
    est_favori = jeux.basculer_favori(nom)
    return jsonify({"succes": True, "favori": est_favori})


@app.route("/api/jeux/supprimer", methods=["POST"])
def api_supprimer_jeu():
    nom = corps_json().get("nom", "")
    succes, message = jeux.supprimer_jeu(nom)
    if succes:
        admin.journaliser("suppression_jeu", nom)
    return jsonify({"succes": succes, "message": message})


@app.route("/api/jeux/deposer", methods=["POST"])
def api_deposer_jeu():
    if "fichier" not in request.files:
        return jsonify({"succes": False, "message": "Aucun fichier reçu."})

    fichier = request.files["fichier"]
    if fichier.filename == "":
        return jsonify({"succes": False, "message": "Aucun fichier sélectionné."})

    extension = os.path.splitext(fichier.filename)[1].lower()
    if extension not in config.EMULATEURS:
        extensions = ", ".join(config.EMULATEURS.keys())
        return jsonify({
            "succes": False,
            "message": f"Format non supporté. Formats acceptés : {extensions}",
        })

    dossier_cible = config.GAMES_DIR if extension in config.EXTENSIONS_SCRATCH else config.ROMS_DIR
    destination = os.path.join(dossier_cible, fichier.filename)

    if os.path.exists(destination):
        return jsonify({"succes": False, "message": "Un jeu avec ce nom existe déjà."})

    try:
        fichier.save(destination)
        admin.journaliser("depot_jeu", fichier.filename)

        # Attribution optionnelle des auteurs au moment du dépôt
        ids_auteurs = request.form.get("auteurs", "")
        if ids_auteurs:
            liste_ids = [i for i in ids_auteurs.split(",") if i]
            eleves.definir_auteurs(fichier.filename, liste_ids)

        return jsonify({"succes": True, "message": f"« {fichier.filename} » a été ajouté."})
    except OSError as erreur:
        return jsonify({"succes": False, "message": f"Erreur lors de l'enregistrement : {erreur}"})


@app.route("/api/jeux/auteurs", methods=["POST"])
def api_definir_auteurs():
    """Modifie la liste des élèves auteurs d'un jeu déjà déposé."""
    donnees = corps_json()
    nom_jeu = donnees.get("nom", "")
    ids_eleves = donnees.get("ids_eleves", [])
    succes, message = eleves.definir_auteurs(nom_jeu, ids_eleves)
    return jsonify({"succes": succes, "message": message})


# ============================================================
#  API — Élèves
# ============================================================
@app.route("/api/eleves")
def api_lister_eleves():
    filtre = request.args.get("q", "")
    classe = request.args.get("classe") or None
    return jsonify(eleves.lister_eleves(filtre, classe))


@app.route("/api/eleves/classes")
def api_liste_classes():
    return jsonify(config.CLASSES_DISPONIBLES)


@app.route("/api/eleves/ajouter", methods=["POST"])
def api_ajouter_eleve():
    donnees = corps_json()
    succes, message, eleve = eleves.ajouter_eleve(donnees.get("nom", ""), donnees.get("classe", ""))
    return jsonify({"succes": succes, "message": message, "eleve": eleve})


@app.route("/api/eleves/modifier", methods=["POST"])
def api_modifier_eleve():
    donnees = corps_json()
    succes, message = eleves.modifier_eleve(
        donnees.get("id", ""), donnees.get("nom"), donnees.get("classe")
    )
    return jsonify({"succes": succes, "message": message})


@app.route("/api/eleves/supprimer", methods=["POST"])
def api_supprimer_eleve():
    donnees = corps_json()
    succes, message = eleves.supprimer_eleve(donnees.get("id", ""))
    if succes:
        admin.journaliser("suppression_eleve", donnees.get("id", ""))
    return jsonify({"succes": succes, "message": message})


@app.route("/api/eleves/jeux/<id_eleve>")
def api_jeux_par_eleve(id_eleve):
    return jsonify(eleves.jeux_par_eleve(id_eleve))


# ============================================================
#  API — Scores / classement
# ============================================================
@app.route("/api/scores/enregistrer", methods=["POST"])
def api_enregistrer_score():
    donnees = corps_json()
    succes, message = scores.enregistrer_score(
        donnees.get("jeu", ""),
        donnees.get("score", 0),
        id_eleve=donnees.get("id_eleve"),
        nom_joueur=donnees.get("nom_joueur", ""),
    )
    if succes:
        admin.journaliser("score_enregistre", f"{donnees.get('jeu', '')} : {donnees.get('score', 0)}")
    return jsonify({"succes": succes, "message": message})


@app.route("/api/scores/jeu/<nom_jeu>")
def api_classement_jeu(nom_jeu):
    limite = request.args.get("limite", 10, type=int)
    return jsonify(scores.classement_pour_jeu(nom_jeu, limite))


@app.route("/api/scores/general")
def api_classement_general():
    limite = request.args.get("limite", 20, type=int)
    return jsonify(scores.classement_general(limite))


# ============================================================
#  API — Manettes
# ============================================================
@app.route("/api/manettes")
def api_lister_manettes():
    return jsonify(manettes.lister_manettes())


# ============================================================
#  API — Système
# ============================================================
@app.route("/api/systeme")
def api_infos_systeme():
    pourcentage, libre_go, total_go = systeme.espace_disque()
    wifi = systeme.etat_wifi()
    return jsonify({
        "heure": systeme.heure_actuelle(),
        "date": systeme.date_actuelle(),
        "wifi": wifi,
        "disque": {"pourcentage": pourcentage, "libre_go": libre_go, "total_go": total_go},
        "temperature": systeme.temperature_cpu(),
        "nb_jeux": len(jeux.lister_tous_les_jeux()),
        "nb_manettes": manettes.nombre_manettes_branchees(),
        "nb_eleves": len(eleves.lister_eleves()),
    })


# ============================================================
#  API — Admin
# ============================================================
@app.route("/api/admin/verifier", methods=["POST"])
def api_verifier_mdp():
    mdp = corps_json().get("mot_de_passe", "")
    return jsonify({"valide": admin.verifier_mot_de_passe(mdp)})


@app.route("/api/admin/changer-mdp", methods=["POST"])
def api_changer_mdp():
    ancien = corps_json().get("ancien", "")
    nouveau = corps_json().get("nouveau", "")
    succes, message = admin.changer_mot_de_passe(ancien, nouveau)
    return jsonify({"succes": succes, "message": message})


@app.route("/api/admin/redemarrer", methods=["POST"])
def api_redemarrer():
    mdp = corps_json().get("mot_de_passe", "")
    if not admin.verifier_mot_de_passe(mdp):
        return jsonify({"succes": False, "message": "Mot de passe incorrect."})
    admin.journaliser("redemarrage")
    os.system("reboot")
    return jsonify({"succes": True, "message": "Redémarrage en cours…"})


@app.route("/api/admin/eteindre", methods=["POST"])
def api_eteindre():
    mdp = corps_json().get("mot_de_passe", "")
    if not admin.verifier_mot_de_passe(mdp):
        return jsonify({"succes": False, "message": "Mot de passe incorrect."})
    admin.journaliser("extinction")
    os.system("shutdown -h now")
    return jsonify({"succes": True, "message": "Extinction en cours…"})


@app.route("/api/admin/journal")
def api_journal():
    lignes = admin.lire_journal(50)
    return jsonify([
        {"date_heure": l[0], "action": l[1], "detail": l[2] if len(l) > 2 else ""}
        for l in lignes
    ])


@app.route("/api/admin/stats")
def api_stats():
    return jsonify(admin.statistiques_jeu_le_plus_lance())


@app.route("/api/admin/sauvegarde/creer", methods=["POST"])
def api_creer_sauvegarde():
    succes, message, chemin = admin.creer_sauvegarde()
    return jsonify({"succes": succes, "message": message})


@app.route("/api/admin/sauvegarde/liste")
def api_liste_sauvegardes():
    return jsonify(admin.lister_sauvegardes())


@app.route("/api/admin/sauvegarde/telecharger/<nom_fichier>")
def api_telecharger_sauvegarde(nom_fichier):
    chemin = os.path.join(config.SAUVEGARDES_DIR, nom_fichier)
    if not os.path.isfile(chemin):
        return "", 404
    return send_file(chemin, as_attachment=True)


@app.route("/api/admin/sauvegarde/restaurer", methods=["POST"])
def api_restaurer_sauvegarde():
    nom_fichier = corps_json().get("nom", "")
    succes, message = admin.restaurer_sauvegarde(nom_fichier)
    return jsonify({"succes": succes, "message": message})


@app.route("/api/admin/sauvegarde/supprimer", methods=["POST"])
def api_supprimer_sauvegarde():
    nom_fichier = corps_json().get("nom", "")
    succes, message = admin.supprimer_sauvegarde(nom_fichier)
    return jsonify({"succes": succes, "message": message})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
