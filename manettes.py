#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
Détection des manettes / joysticks USB branchés sur la borne.

Deux méthodes, dans l'ordre de préférence :
1. pygame.joystick (si le paquet est installé) — donne le nom précis
   de chaque manette.
2. Lecture directe de /dev/input/js* (spécifique Linux) — fonctionne
   sans dépendance supplémentaire, donne juste le nombre de manettes.

Si aucune des deux méthodes ne fonctionne (autre OS, pas de manette,
pas les droits), on renvoie une liste vide sans jamais planter.
"""

import glob
import os


def _detecter_avec_pygame():
    try:
        import pygame
        pygame.init()
        pygame.joystick.init()
        nombre = pygame.joystick.get_count()
        manettes = []
        for i in range(nombre):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            manettes.append({
                "index": i,
                "nom": joystick.get_name(),
                "nb_boutons": joystick.get_numbuttons(),
                "nb_axes": joystick.get_numaxes(),
            })
        pygame.joystick.quit()
        return manettes
    except Exception:
        return None  # pygame indisponible ou erreur : on tente l'autre méthode


def _detecter_avec_dev_input():
    try:
        peripheriques = sorted(glob.glob("/dev/input/js*"))
        return [
            {"index": i, "nom": f"Manette USB ({os.path.basename(chemin)})",
             "nb_boutons": None, "nb_axes": None}
            for i, chemin in enumerate(peripheriques)
        ]
    except OSError:
        return []


def lister_manettes():
    """
    Renvoie une liste de dicts {index, nom, nb_boutons, nb_axes}.
    nb_boutons/nb_axes peuvent être None si l'info n'est pas disponible
    (méthode de repli /dev/input/js*).
    """
    resultat = _detecter_avec_pygame()
    if resultat is not None:
        return resultat
    return _detecter_avec_dev_input()


def nombre_manettes_branchees():
    return len(lister_manettes())
