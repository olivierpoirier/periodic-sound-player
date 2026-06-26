# SoundMaker Prank Console

Prank app for sounds, meme pop-ups, fake alerts, and Windows-style notification jokes. The app starts in English and can switch to French from the top-left menu or the language button.

Author / Auteur : Olivier Poirier

## Ce qui est organise maintenant

- `main.py` lance seulement l'application.
- `qt_app.py` coordonne l'application PySide6/Qt, les reglages et le timer.
- `qt_theme.py`, `qt_backdrop.py`, `qt_widgets.py`, `qt_dialogs.py` et `qt_update_service.py` isolent le theme, le fond anime, les petits widgets, les dialogues et la verification des mises a jour.
- `assets/prank-garden-background.png` est le fond artistique principal de l'interface Qt.
- `app_config.py` regroupe les modes, traductions EN/FR, extensions supportees, l'URL Ko-fi et la source GitHub des mises a jour.
- `asset_library.py` gere les dossiers `Images`, `Sounds` et le cache des fichiers.
- `audio_manager.py` gere pygame et les sons systeme Windows.
- `data/meme_presets.txt` garde les anciens textes simples; `data/meme_templates.json` sauvegarde les nouveaux templates avec texte du haut et texte du bas.
- `data/preferences.json` conserve la langue, les choix de mode et les reglages importants.
- `update_manager.py` verifie les Releases GitHub sans bloquer l'interface.

## Modes disponibles

- Random sounds / Sons aleatoires
- Single sound / Son unique
- Meme pop-up / Pop-up meme
- Fake error / Fausse erreur
- Chaos
- Windows error sound / Son erreur Windows
- Chat notification / Notification chat

Le mode choisi a droite controle les options affichees a gauche.

## Fichiers et categories

Au premier lancement, l'app ne cree que trois dossiers de base :

- `Images/` pour les images et GIFs
- `Sounds/` pour les sons `.mp3`, `.wav`, `.ogg`

Les sous-dossiers deviennent des categories dans l'application. Le scan des dossiers se fait au lancement, apres import, ou avec `Refresh/Rafraichir`; le timer utilise ensuite les listes en memoire.

## Ko-fi

Modifie `KO_FI_URL` dans `app_config.py` pour mettre ta page Ko-fi. Dans l'app, le bouton apparait comme `Buy me a coffee` / `M'acheter un café`.

## Installation

```bash
pip install -r requirements.txt
python main.py
```
