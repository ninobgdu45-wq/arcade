#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
Gestion des jeux : Scratch (.sb3) et ROMs d'émulateurs.
Fournit : liste, recherche, favoris, suppression, ajout, lancement.
"""

import os
import json
import shutil
import subprocess
import time

import config
import eleves as module_eleves


# ============================================================
#  Favoris (persistés en JSON)
# ============================================================
def charger_favoris():
    if not os.path.exists(config.FAVORIS_FILE):
        return []
    try:
        with open(config.FAVORIS_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def sauver_favoris(favoris):
    try:
        with open(config.FAVORIS_FILE, "w", encoding="utf8") as f:
            json.dump(favoris, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def basculer_favori(nom_fichier):
    """Ajoute ou retire un jeu des favoris. Renvoie True si désormais favori."""
    favoris = charger_favoris()
    if nom_fichier in favoris:
        favoris.remove(nom_fichier)
        sauver_favoris(favoris)
        return False
    favoris.append(nom_fichier)
    sauver_favoris(favoris)
    return True


def est_favori(nom_fichier):
    return nom_fichier in charger_favoris()


# ============================================================
#  Inventaire des jeux
# ============================================================
def _dossier_pour_extension(ext):
    if ext in config.EXTENSIONS_SCRATCH:
        return config.GAMES_DIR
    return config.ROMS_DIR


def lister_tous_les_jeux(filtre_texte=""):
    """
    Renvoie une liste de dicts :
    { nom, chemin, extension, type, favori, taille_ko, date_ajout }
    triée : favoris d'abord, puis ordre alphabétique.
    """
    jeux = []
    favoris = charger_favoris()
    filtre_texte = filtre_texte.strip().lower()

    for dossier in (config.GAMES_DIR, config.ROMS_DIR):
        if not os.path.isdir(dossier):
            continue
        for nom in os.listdir(dossier):
            chemin = os.path.join(dossier, nom)
            if not os.path.isfile(chemin):
                continue
            ext = os.path.splitext(nom)[1].lower()
            if ext not in config.EMULATEURS:
                continue
            if filtre_texte and filtre_texte not in nom.lower():
                continue
            try:
                stat = os.stat(chemin)
                taille_ko = round(stat.st_size / 1024, 1)
                date_ajout = time.strftime("%d/%m/%Y", time.localtime(stat.st_mtime))
            except OSError:
                taille_ko, date_ajout = 0, "?"

            jeux.append({
                "nom": nom,
                "chemin": chemin,
                "extension": ext,
                "type": config.EMULATEURS[ext]["nom"],
                "favori": nom in favoris,
                "taille_ko": taille_ko,
                "date_ajout": date_ajout,
                "auteurs": module_eleves.obtenir_auteurs(nom),
            })

    jeux.sort(key=lambda j: (not j["favori"], j["nom"].lower()))
    return jeux


def deposer_jeu(chemin_source):
    """
    Copie un fichier de jeu (.sb3 ou ROM) dans le bon dossier.
    Renvoie (succès: bool, message: str).
    """
    ext = os.path.splitext(chemin_source)[1].lower()
    if ext not in config.EMULATEURS:
        extensions = ", ".join(config.EMULATEURS.keys())
        return False, f"Type de fichier non supporté. Formats acceptés : {extensions}"

    dossier_cible = _dossier_pour_extension(ext)
    destination = os.path.join(dossier_cible, os.path.basename(chemin_source))

    if os.path.exists(destination):
        return False, "Un jeu avec ce nom existe déjà."

    try:
        shutil.copy(chemin_source, destination)
        return True, f"« {os.path.basename(chemin_source)} » a été ajouté."
    except OSError as erreur:
        return False, f"Impossible de copier le fichier : {erreur}"


def supprimer_jeu(nom_fichier):
    """Supprime un jeu de son dossier, de ses favoris, attributions et scores."""
    for dossier in (config.GAMES_DIR, config.ROMS_DIR):
        chemin = os.path.join(dossier, nom_fichier)
        if os.path.exists(chemin):
            try:
                os.remove(chemin)
                favoris = charger_favoris()
                if nom_fichier in favoris:
                    favoris.remove(nom_fichier)
                    sauver_favoris(favoris)
                module_eleves.nettoyer_attribution_jeu(nom_fichier)
                try:
                    import scores as module_scores
                    module_scores.supprimer_scores_jeu(nom_fichier)
                except ImportError:
                    pass
                return True, f"« {nom_fichier} » a été supprimé."
            except OSError as erreur:
                return False, f"Suppression impossible : {erreur}"
    return False, "Fichier introuvable."


def lancer_jeu(nom_fichier, callback_log=None):
    """
    Lance le jeu avec l'émulateur adapté à son extension.
    callback_log(nom_fichier) est appelé en cas de succès, pour journaliser.
    Renvoie (succès, message).
    """
    ext = os.path.splitext(nom_fichier)[1].lower()
    if ext not in config.EMULATEURS:
        return False, "Format de jeu non reconnu."

    dossier = _dossier_pour_extension(ext)
    chemin = os.path.join(dossier, nom_fichier)
    if not os.path.exists(chemin):
        return False, "Le fichier du jeu n'existe plus."

    commande = config.EMULATEURS[ext]["commande"] + [chemin]
    try:
        subprocess.Popen(commande)
        if callback_log:
            callback_log(nom_fichier)
        return True, f"Lancement de « {nom_fichier} »…"
    except FileNotFoundError:
        return False, f"Le programme « {commande[0]} » n'est pas installé sur cette borne."
    except OSError as erreur:
        return False, f"Impossible de lancer le jeu : {erreur}"
