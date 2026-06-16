#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
Gestion des scores et du classement (leaderboard).

Chaque score est enregistré comme :
    { "jeu": nom_fichier, "id_eleve": id ou None, "nom_joueur": str,
      "score": int, "date": "JJ/MM/AAAA HH:MM" }

Les scores sont stockés tous ensemble dans SCORES_FILE (liste JSON).
Le classement par jeu et le classement général se calculent à la volée.
"""

import os
import json
import time

import config
import eleves as module_eleves


def _charger_scores():
    if not os.path.exists(config.SCORES_FILE):
        return []
    try:
        with open(config.SCORES_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _sauver_scores(scores):
    try:
        with open(config.SCORES_FILE, "w", encoding="utf8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def enregistrer_score(nom_jeu, score, id_eleve=None, nom_joueur=""):
    """
    Ajoute un score. Si id_eleve est fourni, nom_joueur est déduit
    automatiquement du nom de l'élève (sinon nom_joueur libre, ex: "Anonyme").
    """
    try:
        score = int(score)
    except (TypeError, ValueError):
        return False, "Le score doit être un nombre entier."

    if id_eleve:
        eleve = module_eleves.obtenir_eleve(id_eleve)
        if eleve:
            nom_joueur = f"{eleve['nom']} ({eleve['classe']})"

    if not nom_joueur:
        nom_joueur = "Anonyme"

    scores = _charger_scores()
    scores.append({
        "jeu": nom_jeu,
        "id_eleve": id_eleve,
        "nom_joueur": nom_joueur,
        "score": score,
        "date": time.strftime("%d/%m/%Y %H:%M"),
    })
    if not _sauver_scores(scores):
        return False, "Erreur lors de l'enregistrement du score."
    return True, "Score enregistré."


def classement_pour_jeu(nom_jeu, limite=10):
    """Renvoie les meilleurs scores pour un jeu donné, triés décroissant."""
    scores = [s for s in _charger_scores() if s["jeu"] == nom_jeu]
    scores.sort(key=lambda s: -s["score"])
    return scores[:limite]


def classement_general(limite=20):
    """
    Renvoie le meilleur score de chaque joueur, toutes parties confondues,
    trié décroissant.
    """
    scores = _charger_scores()
    meilleurs_par_joueur = {}
    for s in scores:
        cle = s.get("id_eleve") or s["nom_joueur"]
        if cle not in meilleurs_par_joueur or s["score"] > meilleurs_par_joueur[cle]["score"]:
            meilleurs_par_joueur[cle] = s

    classement = sorted(meilleurs_par_joueur.values(), key=lambda s: -s["score"])
    return classement[:limite]


def supprimer_scores_jeu(nom_jeu):
    """Supprime tous les scores liés à un jeu (ex: quand le jeu est supprimé)."""
    scores = _charger_scores()
    nouveaux = [s for s in scores if s["jeu"] != nom_jeu]
    _sauver_scores(nouveaux)
