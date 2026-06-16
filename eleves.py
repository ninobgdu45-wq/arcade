#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
Gestion des élèves et attribution des jeux.

Un élève a : un identifiant unique, un nom, une classe.
Un jeu (identifié par son nom de fichier) peut être attribué à un ou
plusieurs élèves (les "auteurs" du jeu déposé), via attributions.json :
    { "nom_du_jeu.sb3": ["id_eleve_1", "id_eleve_2"], ... }
"""

import os
import json
import uuid

import config


# ============================================================
#  Élèves (CRUD)
# ============================================================
def _charger_eleves():
    if not os.path.exists(config.ELEVES_FILE):
        return []
    try:
        with open(config.ELEVES_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _sauver_eleves(eleves):
    try:
        with open(config.ELEVES_FILE, "w", encoding="utf8") as f:
            json.dump(eleves, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def lister_eleves(filtre_texte="", classe=None):
    """Renvoie la liste des élèves, triés par classe puis par nom."""
    eleves = _charger_eleves()
    filtre_texte = filtre_texte.strip().lower()

    if filtre_texte:
        eleves = [e for e in eleves if filtre_texte in e["nom"].lower()]
    if classe:
        eleves = [e for e in eleves if e["classe"] == classe]

    eleves.sort(key=lambda e: (e.get("classe", ""), e["nom"].lower()))
    return eleves


def obtenir_eleve(id_eleve):
    for eleve in _charger_eleves():
        if eleve["id"] == id_eleve:
            return eleve
    return None


def ajouter_eleve(nom, classe):
    nom = nom.strip()
    classe = classe.strip()
    if not nom:
        return False, "Le nom de l'élève ne peut pas être vide.", None
    if not classe:
        return False, "La classe doit être renseignée.", None

    eleves = _charger_eleves()
    if any(e["nom"].lower() == nom.lower() and e["classe"] == classe for e in eleves):
        return False, "Un élève avec ce nom existe déjà dans cette classe.", None

    nouvel_eleve = {"id": uuid.uuid4().hex[:8], "nom": nom, "classe": classe}
    eleves.append(nouvel_eleve)
    if not _sauver_eleves(eleves):
        return False, "Erreur lors de l'enregistrement.", None
    return True, f"« {nom} » a été ajouté à la classe {classe}.", nouvel_eleve


def modifier_eleve(id_eleve, nom=None, classe=None):
    eleves = _charger_eleves()
    for eleve in eleves:
        if eleve["id"] == id_eleve:
            if nom:
                eleve["nom"] = nom.strip()
            if classe:
                eleve["classe"] = classe.strip()
            _sauver_eleves(eleves)
            return True, "Élève mis à jour."
    return False, "Élève introuvable."


def supprimer_eleve(id_eleve):
    eleves = _charger_eleves()
    nouveaux = [e for e in eleves if e["id"] != id_eleve]
    if len(nouveaux) == len(eleves):
        return False, "Élève introuvable."
    _sauver_eleves(nouveaux)
    # Retire l'élève de toutes les attributions existantes
    attributions = _charger_attributions()
    for nom_jeu in list(attributions.keys()):
        if id_eleve in attributions[nom_jeu]:
            attributions[nom_jeu].remove(id_eleve)
    _sauver_attributions(attributions)
    return True, "Élève supprimé."


# ============================================================
#  Attribution des jeux aux élèves
# ============================================================
def _charger_attributions():
    if not os.path.exists(config.ATTRIBUTIONS_FILE):
        return {}
    try:
        with open(config.ATTRIBUTIONS_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _sauver_attributions(attributions):
    try:
        with open(config.ATTRIBUTIONS_FILE, "w", encoding="utf8") as f:
            json.dump(attributions, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def obtenir_auteurs(nom_jeu):
    """Renvoie la liste des élèves (dicts complets) attribués à un jeu."""
    attributions = _charger_attributions()
    ids = attributions.get(nom_jeu, [])
    auteurs = []
    for id_eleve in ids:
        eleve = obtenir_eleve(id_eleve)
        if eleve:
            auteurs.append(eleve)
    return auteurs


def definir_auteurs(nom_jeu, ids_eleves):
    """Remplace la liste des auteurs d'un jeu par la liste fournie."""
    attributions = _charger_attributions()
    attributions[nom_jeu] = list(ids_eleves)
    _sauver_attributions(attributions)
    return True, "Auteurs mis à jour."


def jeux_par_eleve(id_eleve):
    """Renvoie la liste des noms de jeux attribués à un élève donné."""
    attributions = _charger_attributions()
    return [nom_jeu for nom_jeu, ids in attributions.items() if id_eleve in ids]


def nettoyer_attribution_jeu(nom_jeu):
    """Supprime l'entrée d'attribution d'un jeu (ex: quand le jeu est supprimé)."""
    attributions = _charger_attributions()
    if nom_jeu in attributions:
        del attributions[nom_jeu]
        _sauver_attributions(attributions)
