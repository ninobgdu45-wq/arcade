#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
Sécurité et administration :
- mot de passe requis avant extinction / redémarrage / suppression de jeu
- journal (logs) des jeux lancés, horodaté, lisible dans un fichier CSV
"""

import os
import json
import hashlib
import csv
import time
import zipfile
import shutil

import config


# ============================================================
#  Mot de passe admin
# ============================================================
def _hash(mot_de_passe):
    return hashlib.sha256(mot_de_passe.encode("utf8")).hexdigest()


def _charger_admin():
    if not os.path.exists(config.ADMIN_FILE):
        donnees = {"mdp_hash": _hash(config.MDP_ADMIN_DEFAUT)}
        _sauver_admin(donnees)
        return donnees
    try:
        with open(config.ADMIN_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"mdp_hash": _hash(config.MDP_ADMIN_DEFAUT)}


def _sauver_admin(donnees):
    try:
        with open(config.ADMIN_FILE, "w", encoding="utf8") as f:
            json.dump(donnees, f)
    except OSError:
        pass


def verifier_mot_de_passe(saisie):
    donnees = _charger_admin()
    return _hash(saisie) == donnees.get("mdp_hash")


def changer_mot_de_passe(ancien, nouveau):
    if not verifier_mot_de_passe(ancien):
        return False, "Ancien mot de passe incorrect."
    if len(nouveau) < 4:
        return False, "Le nouveau mot de passe doit faire au moins 4 caractères."
    _sauver_admin({"mdp_hash": _hash(nouveau)})
    return True, "Mot de passe mis à jour."


# ============================================================
#  Journal d'utilisation
# ============================================================
def journaliser(action, detail=""):
    """Ajoute une ligne au journal CSV : horodatage, action, détail."""
    nouveau_fichier = not os.path.exists(config.LOGS_FILE)
    try:
        with open(config.LOGS_FILE, "a", newline="", encoding="utf8") as f:
            writer = csv.writer(f)
            if nouveau_fichier:
                writer.writerow(["date_heure", "action", "detail"])
            writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), action, detail])
    except OSError:
        pass


def journaliser_lancement_jeu(nom_fichier):
    journaliser("lancement_jeu", nom_fichier)


def lire_journal(nb_dernieres_lignes=50):
    """Renvoie les dernières lignes du journal, plus récentes en premier."""
    if not os.path.exists(config.LOGS_FILE):
        return []
    try:
        with open(config.LOGS_FILE, "r", encoding="utf8") as f:
            lignes = list(csv.reader(f))
        if len(lignes) <= 1:
            return []
        entetes, donnees = lignes[0], lignes[1:]
        donnees.reverse()
        return donnees[:nb_dernieres_lignes]
    except OSError:
        return []


def statistiques_jeu_le_plus_lance():
    """Renvoie un dict {nom_jeu: nb_lancements} trié par popularité décroissante."""
    compteur = {}
    for ligne in lire_journal(nb_dernieres_lignes=10_000):
        if len(ligne) >= 3 and ligne[1] == "lancement_jeu":
            compteur[ligne[2]] = compteur.get(ligne[2], 0) + 1
    return dict(sorted(compteur.items(), key=lambda x: -x[1]))


# ============================================================
#  Sauvegarde / restauration
# ============================================================
def creer_sauvegarde():
    """
    Crée une archive .zip contenant les jeux, les ROMs et toutes les
    données (favoris, élèves, attributions, scores, journal, mot de passe).
    Renvoie (succès, message, chemin_zip|None).
    """
    horodatage = time.strftime("%Y-%m-%d_%H%M%S")
    nom_zip = f"sauvegarde_{horodatage}.zip"
    chemin_zip = os.path.join(config.SAUVEGARDES_DIR, nom_zip)

    try:
        with zipfile.ZipFile(chemin_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for dossier_source, prefixe in [
                (config.GAMES_DIR, "jeux_scratch"),
                (config.ROMS_DIR, "roms"),
                (config.DATA_DIR, "data"),
            ]:
                if not os.path.isdir(dossier_source):
                    continue
                for racine, _, fichiers in os.walk(dossier_source):
                    for nom_fichier in fichiers:
                        chemin_complet = os.path.join(racine, nom_fichier)
                        chemin_relatif = os.path.relpath(chemin_complet, dossier_source)
                        archive.write(chemin_complet, os.path.join(prefixe, chemin_relatif))
        journaliser("creation_sauvegarde", nom_zip)
        return True, f"Sauvegarde créée : {nom_zip}", chemin_zip
    except OSError as erreur:
        return False, f"Erreur lors de la sauvegarde : {erreur}", None


def lister_sauvegardes():
    """Renvoie la liste des sauvegardes disponibles, triées de la plus récente à la plus ancienne."""
    if not os.path.isdir(config.SAUVEGARDES_DIR):
        return []
    fichiers = []
    for nom in os.listdir(config.SAUVEGARDES_DIR):
        if nom.endswith(".zip"):
            chemin = os.path.join(config.SAUVEGARDES_DIR, nom)
            try:
                stat = os.stat(chemin)
                fichiers.append({
                    "nom": nom,
                    "taille_ko": round(stat.st_size / 1024, 1),
                    "date": time.strftime("%d/%m/%Y %H:%M", time.localtime(stat.st_mtime)),
                })
            except OSError:
                continue
    fichiers.sort(key=lambda f: f["date"], reverse=True)
    return fichiers


def restaurer_sauvegarde(nom_fichier_zip):
    """
    Restaure une sauvegarde .zip existante (écrase les données actuelles).
    Renvoie (succès, message).
    """
    chemin_zip = os.path.join(config.SAUVEGARDES_DIR, nom_fichier_zip)
    if not os.path.isfile(chemin_zip):
        return False, "Fichier de sauvegarde introuvable."

    try:
        with zipfile.ZipFile(chemin_zip, "r") as archive:
            archive.extractall(config.ASSETS_DIR)
        journaliser("restauration_sauvegarde", nom_fichier_zip)
        return True, "Sauvegarde restaurée. Un redémarrage de l'application est recommandé."
    except (zipfile.BadZipFile, OSError) as erreur:
        return False, f"Erreur lors de la restauration : {erreur}"


def supprimer_sauvegarde(nom_fichier_zip):
    chemin_zip = os.path.join(config.SAUVEGARDES_DIR, nom_fichier_zip)
    if not os.path.isfile(chemin_zip):
        return False, "Fichier introuvable."
    try:
        os.remove(chemin_zip)
        return True, "Sauvegarde supprimée."
    except OSError as erreur:
        return False, f"Erreur : {erreur}"
