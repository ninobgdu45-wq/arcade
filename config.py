#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
Configuration centrale de la borne ARCADE.
Toutes les couleurs, chemins et constantes vivent ici pour que
le reste du code n'ait jamais de valeur "en dur".
"""

import os


def _construire_chemins(racine):
    """Construit le dict de tous les chemins dérivés d'un dossier racine."""
    data_dir = os.path.join(racine, "data")
    return {
        "ASSETS_DIR": racine,
        "GAMES_DIR": os.path.join(racine, "jeux_scratch"),
        "ROMS_DIR": os.path.join(racine, "roms"),
        "DATA_DIR": data_dir,
        "SAUVEGARDES_DIR": os.path.join(racine, "sauvegardes"),
        "MUSIQUE_DIR": os.path.join(racine, "musique"),
        "FAVORIS_FILE": os.path.join(data_dir, "favoris.json"),
        "LOGS_FILE": os.path.join(data_dir, "logs.csv"),
        "ADMIN_FILE": os.path.join(data_dir, "admin.json"),
        "ELEVES_FILE": os.path.join(data_dir, "eleves.json"),
        "ATTRIBUTIONS_FILE": os.path.join(data_dir, "attributions.json"),
        "SCORES_FILE": os.path.join(data_dir, "scores.json"),
        "LOGO_PATH": os.path.join(racine, "logo.png"),
        "CC_LOGO_PATH": os.path.join(racine, "droitsCC.png"),
    }


# ============================================================
#  Chemins
# ============================================================
# ASSETS_DIR peut être surchargé par la variable d'environnement
# BORNE_ARCADE_DIR (utile pour tester hors Raspberry Pi, ou si la
# borne n'utilise pas l'utilisateur "pi").
_DOSSIER_PAR_DEFAUT = "/home/pi/arcade"
_racine_choisie = os.environ.get("BORNE_ARCADE_DIR", _DOSSIER_PAR_DEFAUT)
_chemins = _construire_chemins(_racine_choisie)

try:
    for cle in ("GAMES_DIR", "ROMS_DIR", "DATA_DIR", "SAUVEGARDES_DIR", "MUSIQUE_DIR"):
        os.makedirs(_chemins[cle], exist_ok=True)
except OSError as erreur:
    # Si /home/pi/arcade n'est pas accessible (mauvais OS, droits
    # insuffisants, dossier inexistant...), on bascule sur un dossier
    # local au lieu de planter au démarrage du serveur.
    print(f"[config] Impossible d'utiliser {_racine_choisie} ({erreur}).")
    print("[config] Repli sur un dossier local 'arcade_data/'.")
    _racine_choisie = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arcade_data")
    _chemins = _construire_chemins(_racine_choisie)
    for cle in ("GAMES_DIR", "ROMS_DIR", "DATA_DIR", "SAUVEGARDES_DIR", "MUSIQUE_DIR"):
        os.makedirs(_chemins[cle], exist_ok=True)

ASSETS_DIR        = _chemins["ASSETS_DIR"]
GAMES_DIR         = _chemins["GAMES_DIR"]
ROMS_DIR          = _chemins["ROMS_DIR"]
DATA_DIR          = _chemins["DATA_DIR"]
SAUVEGARDES_DIR   = _chemins["SAUVEGARDES_DIR"]
MUSIQUE_DIR       = _chemins["MUSIQUE_DIR"]
FAVORIS_FILE      = _chemins["FAVORIS_FILE"]
LOGS_FILE         = _chemins["LOGS_FILE"]
ADMIN_FILE        = _chemins["ADMIN_FILE"]
ELEVES_FILE       = _chemins["ELEVES_FILE"]
ATTRIBUTIONS_FILE = _chemins["ATTRIBUTIONS_FILE"]
SCORES_FILE       = _chemins["SCORES_FILE"]
LOGO_PATH         = _chemins["LOGO_PATH"]
CC_LOGO_PATH      = _chemins["CC_LOGO_PATH"]

# ============================================================
#  Palette sobre (ardoise + accent orange unique)
# ============================================================
BG        = "#23262b"
PANEL     = "#2c2f36"
PANEL_2   = "#33363e"
BORDER    = "#3a3e46"
ACCENT    = "#e8772e"
ACCENT_DIM = "#a85a22"
TEXT      = "#e7e7ea"
TEXT_DIM  = "#9a9ea6"
DANGER    = "#c84b4b"
SUCCESS   = "#5ea96b"

FONT_TITLE = ("Helvetica", 24, "bold")
FONT_SUB   = ("Helvetica", 11)
FONT_BODY  = ("Helvetica", 10)
FONT_BODY_BOLD = ("Helvetica", 10, "bold")
FONT_SMALL = ("Helvetica", 9)
FONT_MONO  = ("Courier New", 10)

# ============================================================
#  Émulateurs / consoles supportées (extension -> commande)
# ============================================================
EMULATEURS = {
    ".sb3": {"nom": "Scratch", "commande": ["scratch2"]},
    ".nes": {"nom": "NES", "commande": ["retroarch", "-L", "/usr/lib/libretro/fceumm_libretro.so"]},
    ".gba": {"nom": "Game Boy Advance", "commande": ["retroarch", "-L", "/usr/lib/libretro/mgba_libretro.so"]},
    ".gb":  {"nom": "Game Boy", "commande": ["retroarch", "-L", "/usr/lib/libretro/gambatte_libretro.so"]},
}

EXTENSIONS_SCRATCH = (".sb3",)
EXTENSIONS_ROMS    = tuple(e for e in EMULATEURS if e != ".sb3")

# ============================================================
#  Mot de passe admin par défaut (modifiable via l'écran admin)
#  Stocké hashé dans ADMIN_FILE après premier lancement.
# ============================================================
MDP_ADMIN_DEFAUT = "college2024"

# ============================================================
#  Classes du collège (modifiable librement)
# ============================================================
CLASSES_DISPONIBLES = [
    "6A", "6B", "6C", "6D",
    "5A", "5B", "5C", "5D",
    "4A", "4B", "4C", "4D",
    "3A", "3B", "3C", "3D",
]

# ============================================================
#  Éditeur Scratch en ligne (pour le bouton "Créer un jeu")
# ============================================================
URL_EDITEUR_SCRATCH = "https://scratch.mit.edu/projects/editor/"
