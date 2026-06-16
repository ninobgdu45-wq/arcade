#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
Lance le serveur Flask de la borne, puis ouvre Chromium en mode kiosque
sur l'interface. À utiliser pour le démarrage automatique sur le Pi.

Usage : python3 demarrer.py
"""

import subprocess
import time
import webbrowser

URL = "http://localhost:5000"

# Démarre le serveur Flask en arrière-plan
processus_serveur = subprocess.Popen(["python3", "app.py"])

# Laisse le temps au serveur de démarrer
time.sleep(2)

# Essaie d'ouvrir Chromium en kiosque (typique sur Raspberry Pi OS)
try:
    subprocess.Popen([
        "chromium-browser", "--kiosk", "--noerrdialogs",
        "--disable-infobars", "--incognito", URL,
    ])
except FileNotFoundError:
    # Repli : navigateur par défaut, fenêtre normale
    webbrowser.open(URL)

processus_serveur.wait()
