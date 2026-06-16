#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
Informations système affichées sur la borne : heure, wifi, espace disque.
Conçu pour être robuste : si une commande système n'existe pas (ex: sur un
PC de dev qui n'est pas un Raspberry Pi), on renvoie une valeur de repli
plutôt que de planter l'interface.
"""

import shutil
import subprocess
import time


def heure_actuelle():
    return time.strftime("%H:%M:%S")


def date_actuelle():
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
            "août", "septembre", "octobre", "novembre", "décembre"]
    t = time.localtime()
    return f"{jours[t.tm_wday]} {t.tm_mday} {mois[t.tm_mon - 1]} {t.tm_year}"


def espace_disque():
    """Renvoie (pourcentage_utilise, libre_go, total_go)."""
    try:
        total, utilise, libre = shutil.disk_usage("/")
        go = 1024 ** 3
        pourcentage = round((utilise / total) * 100)
        return pourcentage, round(libre / go, 1), round(total / go, 1)
    except OSError:
        return None, None, None


def etat_wifi():
    """
    Renvoie un dict {connecte: bool, ssid: str|None}.
    Utilise `iwgetid`, dispo sur Raspberry Pi OS ; renvoie un état neutre sinon.
    """
    try:
        resultat = subprocess.run(
            ["iwgetid", "-r"], capture_output=True, text=True, timeout=2
        )
        ssid = resultat.stdout.strip()
        if ssid:
            return {"connecte": True, "ssid": ssid}
        return {"connecte": False, "ssid": None}
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return {"connecte": None, "ssid": None}  # statut inconnu (pas sur un Pi)


def temperature_cpu():
    """Renvoie la température CPU en °C (spécifique Raspberry Pi), ou None."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return round(int(f.read().strip()) / 1000, 1)
    except (OSError, ValueError):
        return None
