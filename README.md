# SystemEventMonitor

Un outil d'automatisation de sons et d'alertes visuelles, conçu pour la gestion d'événements périodiques sur Windows.

## 🚀 À propos
**SystemEventMonitor** est une application légère qui permet de déclencher des sons, des messages d'erreur système ou des pop-ups visuels de manière aléatoire sur une plage de temps définie. Que ce soit pour tester des notifications ou pour des besoins de personnalisation d'environnement, cet outil offre une flexibilité totale grâce à son système de catégories et ses modes de configuration avancés.

## ✨ Fonctionnalités principales

- **Gestion par dossiers :** Organisez vos sons et images dans des sous-dossiers ; ils seront automatiquement détectés comme des catégories dans l'application.
- **Minuteur intelligent :** Définissez une plage de temps (min/max) et laissez l'application gérer le prochain événement.
- **Mode Chaos :** Une option pour réduire progressivement le délai entre chaque événement pour une montée en intensité.
- **Mode Camouflage :** Changez le titre de la fenêtre et utilisez la "Boss Key" (ÉCHAP) pour masquer l'application instantanément.
- **Modes de notification variés :**
    - Sons personnalisés (.mp3, .wav, .ogg).
    - Simulation d'erreurs système Windows natives.
    - Sons de notification de chat (ex: Discord/Teams).
- **Interface intuitive :** Configuration facile via onglets avec aide intégrée.

## 🛠️ Installation

1. Clonez ce dépôt ou téléchargez le script.
2. Installez les dépendances nécessaires :
   ```bash
   pip install customtkinter pygame pillow pystray