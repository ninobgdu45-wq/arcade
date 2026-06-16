# Borne ARCADE du collège — version Web (v6.0)

Dépôt des fichiers utiles pour le système d'exploitation de la borne arcade barTop du collège.

Interface web (HTML / CSS / JS) servie par un petit serveur **Python (Flask)**
qui pilote la borne : lancement de jeux Scratch et ROMs, dépôt de nouveaux
jeux, attribution des jeux aux élèves, leaderboard, détection de manettes,
favoris, recherche, infos système, écran de veille, musique d'ambiance, et
administration protégée par mot de passe (sauvegarde/restauration incluse).

Le rendu visuel est un thème **néon sobre** : fond presque noir, un seul
accent cyan électrique, glow discret au survol, jamais clignotant.

---

## Aperçu des fonctionnalités

- **Accueil** : logo, navigation par grandes cartes tactiles, horloge en
  direct, bouton musique d'ambiance, raccourcis clavier rappelés en bas
  d'écran.
- **Bibliothèque de jeux** : liste de tous les jeux déposés (Scratch `.sb3`
  et ROMs `.nes` / `.gb` / `.gba`), recherche en direct, favoris (★),
  auteurs affichés sous chaque jeu, lancement en un clic, enregistrement
  de score, suppression avec confirmation.
- **Dépôt de jeu** : ajout d'un fichier depuis le navigateur, avec
  attribution optionnelle à un ou plusieurs élèves au moment du dépôt.
- **Élèves** : fiches élève (nom + classe), filtre par classe, recherche,
  modification, suppression (nettoie automatiquement ses attributions de
  jeux), nombre de jeux déposés par élève.
- **Classement** : podium des 3 meilleurs scores toutes parties confondues,
  liste complète en dessous, classement par jeu également disponible via
  l'API.
- **Créer un jeu** : accès direct à l'éditeur Scratch en ligne ou à
  Scratch installé localement, rappel de la procédure d'export `.sb3`,
  idées de projets pour démarrer.
- **Manettes** : détection automatique des manettes/joysticks USB
  branchés (via `pygame` si installé, sinon lecture de `/dev/input/js*`),
  affichées sur les écrans Infos système et Administration.
- **Infos système** : date, Wi-Fi, espace disque, température CPU,
  nombre de jeux, manettes branchées, élèves référencés — rafraîchi
  toutes les 5 secondes.
- **Écran de veille** : apparaît après 90 secondes d'inactivité (logo qui
  flotte, horloge, stats), disparaît au moindre clic/touche.
- **Musique d'ambiance** : lecture en boucle des pistes déposées dans le
  dossier `musique/`, activable/désactivable depuis l'accueil (coupée par
  défaut, conformément aux règles d'autoplay des navigateurs).
- **Administration** (protégée par mot de passe) : redémarrer/éteindre la
  borne, changer le mot de passe, consulter le journal des 50 dernières
  actions, voir les jeux les plus lancés, voir les manettes branchées,
  **créer une sauvegarde .zip** de toute la bibliothèque et des données,
  **télécharger / restaurer / supprimer** des sauvegardes existantes.
- **Raccourcis clavier globaux** (depuis l'écran d'accueil) :
  - `S` → ouvre Scratch
  - `R` → redémarre la borne (mot de passe requis)
  - `E` → éteint la borne (mot de passe requis)

Mot de passe administrateur par défaut : **`college2024`**
(à changer dès l'installation depuis l'écran *Administration*).

---

## Structure du projet

```
borne_web/
├── app.py              → serveur Flask : routes pages + API JSON
├── config.py           → chemins, palette de couleurs, émulateurs, classes
├── jeux.py             → logique métier : lister / déposer / supprimer / lancer / favoris
├── eleves.py           → CRUD élèves + attribution des jeux (auteurs)
├── scores.py           → enregistrement des scores + classement (leaderboard)
├── manettes.py         → détection des manettes/joysticks USB
├── systeme.py          → infos système : heure, wifi, disque, température
├── admin.py            → mot de passe (hashé), journal, sauvegarde/restauration
├── demarrer.py         → lance Flask + ouvre le navigateur en mode kiosque
├── templates/
│   ├── base.html         → squelette commun (police, CSS, JS, veille, audio)
│   ├── accueil.html      → écran d'accueil
│   ├── bibliotheque.html → écran liste des jeux + scores + auteurs
│   ├── eleves.html       → gestion des élèves
│   ├── classement.html   → podium + classement général
│   ├── creer.html        → éditeur Scratch + tutos
│   ├── systeme.html      → écran infos système
│   └── admin.html        → administration + sauvegardes + manettes
└── static/
    ├── css/style.css     → thème néon sobre
    └── js/commun.js      → horloge, toasts, modals, veille, musique
```

---

## Installation sur la borne (Raspberry Pi)

### 1. Pré-requis

```bash
sudo apt update
sudo apt install python3 python3-pip chromium-browser
pip3 install flask
```

Pour la détection précise des manettes (nom exact, nombre de boutons) :

```bash
pip3 install pygame
```

Sans `pygame`, la détection bascule automatiquement sur la lecture de
`/dev/input/js*` (fonctionne aussi, donne juste un nom générique).

### 2. Emplacement des fichiers

Copier tout le dossier `borne_web/` sur la borne, par exemple dans
`/home/pi/arcade/` :

```
/home/pi/arcade/
├── app.py
├── config.py
├── jeux.py
├── eleves.py
├── scores.py
├── manettes.py
├── systeme.py
├── admin.py
├── demarrer.py
├── logo.png            ← à ajouter
├── droitsCC.png         ← à ajouter
├── templates/
└── static/
```

Les images `logo.png` et `droitsCC.png` doivent être placées directement
dans `/home/pi/arcade/` (à côté de `app.py`). Elles sont servies par Flask
via la route `/assets/<nom_fichier>`.

Pour la musique d'ambiance, déposer des fichiers `.mp3`, `.ogg` ou `.wav`
dans `/home/pi/arcade/musique/`.

Les dossiers suivants sont créés automatiquement au premier lancement s'ils
n'existent pas :

- `/home/pi/arcade/jeux_scratch/` — projets Scratch déposés
- `/home/pi/arcade/roms/` — ROMs déposées
- `/home/pi/arcade/data/` — favoris, élèves, attributions, scores, mot de
  passe, journal
- `/home/pi/arcade/sauvegardes/` — archives .zip créées par l'écran admin
- `/home/pi/arcade/musique/` — pistes audio d'ambiance

### 3. Lancement manuel (test)

```bash
cd /home/pi/arcade
python3 app.py
```

Puis ouvrir un navigateur sur `http://localhost:5000`.

### 4. Lancement en mode kiosque (utilisation normale)

```bash
python3 demarrer.py
```

Ce script démarre le serveur Flask en arrière-plan, attend 2 secondes, puis
ouvre Chromium en plein écran sans barre d'adresse (`--kiosk`). Si Chromium
n'est pas installé, il bascule sur le navigateur par défaut en fenêtre
normale.

### 5. Démarrage automatique au boot (optionnel)

Pour que la borne lance l'interface toute seule à l'allumage, ajouter au
fichier `/etc/xdg/autostart/borne-arcade.desktop` (ou via crontab `@reboot`) :

```ini
[Desktop Entry]
Type=Application
Name=Borne Arcade
Exec=python3 /home/pi/arcade/demarrer.py
X-GNOME-Autostart-enabled=true
```

---

## Émulateurs / formats supportés

Configurable dans `config.py`, dictionnaire `EMULATEURS` :

| Extension | Console            | Commande lancée                                          |
|-----------|---------------------|------------------------------------------------------------|
| `.sb3`    | Scratch              | `scratch2 <fichier>`                                       |
| `.nes`    | NES                  | `retroarch -L .../fceumm_libretro.so <fichier>`             |
| `.gba`    | Game Boy Advance      | `retroarch -L .../mgba_libretro.so <fichier>`               |
| `.gb`     | Game Boy              | `retroarch -L .../gambatte_libretro.so <fichier>`            |

Si `retroarch` n'est pas installé sur la borne, retirer les lignes
correspondantes dans `EMULATEURS` (seul Scratch restera disponible) ou
installer RetroArch et les cores libretro nécessaires :

```bash
sudo apt install retroarch libretro-fceumm libretro-mgba libretro-gambatte
```

**Important** : vérifier que la commande `scratch2` accepte bien un chemin
de fichier `.sb3` en argument pour l'ouvrir directement. Si la syntaxe
réelle sur la borne est différente, ajuster la valeur de `commande` dans
`config.py`.

---

## Élèves et attribution des jeux

Les classes proposées par défaut (6A à 3D) sont définies dans
`config.py`, variable `CLASSES_DISPONIBLES` — à adapter à l'organisation
réelle du collège.

Un jeu peut avoir plusieurs auteurs (travail de groupe). L'attribution se
fait soit au moment du dépôt (écran d'accueil), soit après coup via l'API
`/api/jeux/auteurs`. Supprimer un élève retire automatiquement ses
attributions, sans toucher au fichier du jeu lui-même.

## Scores et classement

Un score peut être associé à un élève (le nom affiché devient
« Nom (Classe) ») ou enregistré en « Joueur anonyme / invité ». Le
classement général retient le meilleur score de chaque joueur, toutes
parties confondues. Le classement par jeu (`/api/scores/jeu/<nom>`) n'est
pas encore affiché dans une page dédiée — actuellement disponible via
l'API si besoin d'un futur écran « scores de ce jeu ».

## Sauvegarde et restauration

Le bouton **Créer une sauvegarde** (écran Administration) génère une
archive `.zip` horodatée contenant tous les jeux Scratch, toutes les ROMs,
et toutes les données (élèves, attributions, scores, favoris, mot de
passe, journal). Le bouton **Gérer les sauvegardes** permet de télécharger,
restaurer ou supprimer une sauvegarde existante.

Restaurer une sauvegarde **écrase** les données actuelles : à utiliser
avec précaution, idéalement après avoir créé une sauvegarde de l'état
courant au préalable.

---

## Sécurité

- Le mot de passe administrateur est stocké **hashé** (SHA-256) dans
  `data/admin.json`, jamais en clair.
- Les actions sensibles (redémarrage, extinction, suppression de jeu,
  d'élève, restauration) sont toutes journalisées dans `data/logs.csv`
  avec horodatage.
- Le serveur Flask tourne par défaut sur `0.0.0.0:5000`, donc accessible
  depuis le réseau local. Si la borne est sur un réseau partagé (Wi-Fi du
  collège), envisager de restreindre l'écoute à `127.0.0.1` dans
  `app.py` (`app.run(host="127.0.0.1", port=5000)`) si l'accès distant
  n'est pas souhaité.

---

## Personnalisation

- **Couleurs / police** : tout est centralisé dans
  `static/css/style.css` (variables CSS en haut du fichier) et
  `config.py` côté Python pour les valeurs encore utilisées côté serveur.
- **Mot de passe par défaut** : modifiable dans `config.py`
  (`MDP_ADMIN_DEFAUT`), pris en compte uniquement avant la création du
  premier `data/admin.json`.
- **Ajouter une console/émulateur** : ajouter une entrée dans le
  dictionnaire `EMULATEURS` de `config.py`.
- **Classes du collège** : modifier la liste `CLASSES_DISPONIBLES` dans
  `config.py`.
- **Délai avant écran de veille** : modifier `DELAI_VEILLE_MS` en haut de
  `static/js/commun.js` (en millisecondes, 90000 = 90 secondes).

---

## Dépannage

| Symptôme                                   | Piste                                                          |
|---------------------------------------------|------------------------------------------------------------------|
| Page blanche / erreur Flask au démarrage    | Vérifier `pip3 install flask` et la version de Python (3.7+)     |
| Logo ne s'affiche pas                        | Vérifier que `logo.png` est bien dans `/home/pi/arcade/`         |
| « Scratch n'est pas installé »              | Vérifier que la commande `scratch2` existe dans le `PATH`        |
| Wi-Fi toujours « Statut inconnu »            | La commande `iwgetid` n'est pas disponible (pas un Raspberry Pi)|
| Température CPU « Indisponible »            | Fichier `/sys/class/thermal/thermal_zone0/temp` absent (normal hors Raspberry Pi) |
| Mot de passe oublié                          | Supprimer `data/admin.json` : le mot de passe repasse à la valeur par défaut au prochain lancement |
| Aucune manette détectée alors qu'elle est branchée | Installer `pygame` (`pip3 install pygame`) pour une détection plus fiable que `/dev/input/js*` |
| Musique d'ambiance ne se lance pas automatiquement | Comportement normal : les navigateurs bloquent l'autoplay audio, il faut cliquer sur le bouton 🔇 Musique une première fois |
| Erreur 500 générale                          | Le détail exact du problème s'affiche désormais dans la console où tourne `python3 app.py` |

---

## Historique des versions

- **v1.x** : interface Tkinter minimale (label + boutons clavier R/S/E).
- **v3.0** : Tkinter, thème sobre, dépôt/lancement de jeux Scratch.
- **v4.0** : Tkinter, application complète multi-écrans (favoris,
  recherche, infos système, admin, journal).
- **v5.0** : portage en interface web (Flask + HTML/CSS/JS), thème néon
  sobre, même ensemble de fonctionnalités que la v4.0, gestion d'erreurs
  robuste (plus de 500 muet).
- **v6.0** *(actuelle)* : élèves et attribution des jeux, scores et
  classement (leaderboard), détection des manettes USB, écran de veille
  avec stats, musique d'ambiance, sauvegarde/restauration en .zip,
  accès direct à l'éditeur Scratch.
