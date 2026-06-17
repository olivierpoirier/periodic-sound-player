import os
import sys
import random
import shutil
import threading
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog
import subprocess

# Désactiver le message de bienvenue de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import customtkinter as ctk
from PIL import Image, ImageTk, ImageSequence
import pystray

# Importation sécurisée pour les sons systèmes Windows
try:
    import winsound
except ImportError:
    winsound = None

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SoundMakerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- CHEMINS ET CONFIGURATION ---
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.LIST_IMAGES_PATH = os.path.join(self.BASE_DIR, "Images")
        self.LIST_SOUNDS_PATH = os.path.join(self.BASE_DIR, "Sounds")
        
        # S'assurer que les dossiers de base existent
        os.makedirs(self.LIST_IMAGES_PATH, exist_ok=True)
        os.makedirs(self.LIST_SOUNDS_PATH, exist_ok=True)
        
        pygame.mixer.init()

        # --- DICTIONNAIRE DE TRADUCTION ---
        self.lang = "fr"
        self.texts = {
            "fr": {
                "title": "SoundMaker Pro",
                "stealth_title": "Host Process for Windows Tasks",
                "boss_key": "🤫 Boss Key : ÉCHAP pour tout cacher",
                "no_img": "Aucune image",
                "add_img": "➕ Importer Image/GIF",
                "tab_audio": "⏱️ Audio & Timer",
                "tab_pranks": "🤡 Farces",
                "tab_settings": "⚙️ Réglages",
                "tab_help": "📖 Aide & Dossiers",
                "min_time": "Temps minimum : {} min",
                "max_time": "Temps maximum : {} min",
                "vol": "🔊 Volume : {}%",
                "add_sound": "🎵 Importer un Son",
                "play_test": "⚡ Tester un son maintenant",
                "chaos": "🔥 Mode Chaos (Accélération)",
                "stealth": "🥷 Mode Camouflage Windows",
                "meme_switch": "🖼️ Pop-up Meme (Fenêtre flottante)",
                "meme_dur": "Durée : {:.1f} sec",
                "err_switch": "💬 Fausse Erreur Système",
                "btn_preview": "👁️ Prévisualiser",
                "lang_switch": "🌍 Passer en Anglais",
                "next_event": "Prochain événement : {:02d}m {:02d}s",
                "popup_title": "Alerte Système",
                "btn_ok": "OK",
                "btn_recalc": "🔄 Recalculer le minuteur",
                "switch_mute": "🔇 Mode Silencieux (Pop-ups seuls)",
                "switch_win_err": "💻 Son d'erreur Windows uniquement",
                "switch_chat_notif": "💬 Son Notification Chat (Discord/Teams)",
                "folder_img": "📁 Catégorie Images :",
                "folder_snd": "📁 Catégorie Sons :",
                "btn_open_img_dir": "📂 Ouvrir le dossier Images",
                "btn_open_snd_dir": "📂 Ouvrir le dossier Sons",
                "help_text": (
                    "=== GUIDE D'UTILISATION ===\n\n"
                    "1. GESTION DES FICHIERS\n"
                    "L'application crée automatiquement deux dossiers ('Images' et 'Sounds') au même "
                    "endroit que ce script. Utilise les boutons ci-dessus pour les ouvrir directement.\n"
                    "- Tu peux glisser tes fichiers directement dans ces dossiers.\n"
                    "- Si tu crées des sous-dossiers (ex: Sounds/Discord), ils deviendront des 'Catégories' "
                    "dans l'application !\n\n"
                    "2. BOUTONS D'IMPORTATION (➕ / 🎵)\n"
                    "Ils permettent de copier des fichiers depuis tes Téléchargements (ou ailleurs) "
                    "directement dans le dossier de l'application. Tu n'es pas obligé de les utiliser "
                    "si tu préfères gérer tes dossiers à la main.\n\n"
                    "3. LES MODES DE JEU\n"
                    "- Mode Chaos : Le temps entre chaque son se réduit de 25% à chaque fois. Fait pour rendre fou.\n"
                    "- Mode Silencieux : Coupe l'audio. Idéal si tu veux juste faire spawner des images (Meme).\n"
                    "- Mode Camouflage : Change le nom de la fenêtre et son icône pour passer inaperçu.\n"
                    "- Boss Key (ÉCHAP) : Fait disparaître la fenêtre instantanément. Retrouve-la dans la zone "
                    "de notification (en bas à droite près de l'heure)."
                )
            },
            "en": {
                "title": "SoundMaker Pro",
                "stealth_title": "Host Process for Windows Tasks",
                "boss_key": "🤫 Boss Key: ESC to hide everything",
                "no_img": "No image",
                "add_img": "➕ Import Image/GIF",
                "tab_audio": "⏱️ Audio & Timer",
                "tab_pranks": "🤡 Pranks",
                "tab_settings": "⚙️ Settings",
                "tab_help": "📖 Help & Folders",
                "min_time": "Minimum time: {} min",
                "max_time": "Maximum time: {} min",
                "vol": "🔊 Volume: {}%",
                "add_sound": "🎵 Import Sound",
                "play_test": "⚡ Test sound now",
                "chaos": "🔥 Chaos Mode (Acceleration)",
                "stealth": "🥷 Windows Stealth Mode",
                "meme_switch": "🖼️ Meme Pop-up (Floating Window)",
                "meme_dur": "Duration: {:.1f} sec",
                "err_switch": "💬 Fake System Error",
                "btn_preview": "👁️ Preview",
                "lang_switch": "🌍 Switch to French",
                "next_event": "Next event: {:02d}m {:02d}s",
                "popup_title": "System Alert",
                "btn_ok": "OK",
                "btn_recalc": "🔄 Recalculate Timer",
                "switch_mute": "🔇 Mute Sound (Pop-ups only)",
                "switch_win_err": "💻 Windows Error Sound Only",
                "switch_chat_notif": "💬 Chat Notification Sound (Discord)",
                "folder_img": "📁 Image Category:",
                "folder_snd": "📁 Sound Category:",
                "btn_open_img_dir": "📂 Open Images Folder",
                "btn_open_snd_dir": "📂 Open Sounds Folder",
                "help_text": (
                    "=== USER GUIDE ===\n\n"
                    "1. FILE MANAGEMENT\n"
                    "The app automatically creates two folders ('Images' and 'Sounds') next to this script. "
                    "Use the buttons above to open them directly in your file explorer.\n"
                    "- You can drag and drop your files directly into these folders.\n"
                    "- If you create subfolders (e.g., Sounds/Discord), they will become selectable 'Categories'!\n\n"
                    "2. IMPORT BUTTONS (➕ / 🎵)\n"
                    "These copy files from your Downloads (or elsewhere) directly into the app's folders. "
                    "You don't have to use them if you prefer managing files manually.\n\n"
                    "3. GAME MODES\n"
                    "- Chaos Mode: The time between each event reduces by 25% every trigger.\n"
                    "- Mute Mode: Cuts all audio. Perfect if you only want visual pop-ups (Memes).\n"
                    "- Stealth Mode: Changes window name and icon to look like a boring system process.\n"
                    "- Boss Key (ESC): Instantly hides the app. You can restore it from the system tray "
                    "(bottom right near the clock)."
                )
            }
        }

        # --- ÉTAT DE L'APPLICATION ---
        self.selected_img_folder = ""
        self.selected_snd_folder = ""
        
        self.list_of_images = []
        self.list_of_sounds = []
        
        self.current_image_index = 0
        self.next_play_time = datetime.now()
        self.tray_icon = None
        self.chaos_factor = 1.0
        
        self.main_anim_id = None
        self.main_gif_frames = []
        self.main_gif_delay = 100

        # --- FENÊTRE ---
        self.title(self.texts[self.lang]["title"])
        self.geometry("950x580") # Un peu élargi pour s'accommoder du texte
        self.resizable(False, False)

        self.bind("<Escape>", lambda event: self.boss_key_trigger())
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        self.refresh_directories()
        self.setup_ui()
        self.setup_system_tray()
        self.update_language()
        self.schedule_next_sound()
        self.sound_director_loop()

    def get_subfolders(self, base_path):
        subs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
        return ["/"] + subs

    def refresh_directories(self):
        self.img_subfolders = self.get_subfolders(self.LIST_IMAGES_PATH)
        self.snd_subfolders = self.get_subfolders(self.LIST_SOUNDS_PATH)
        
        if self.selected_img_folder not in self.img_subfolders:
            self.selected_img_folder = "/"
        if self.selected_snd_folder not in self.snd_subfolders:
            self.selected_snd_folder = "/"

        img_target = self.LIST_IMAGES_PATH if self.selected_img_folder == "/" else os.path.join(self.LIST_IMAGES_PATH, self.selected_img_folder)
        snd_target = self.LIST_SOUNDS_PATH if self.selected_snd_folder == "/" else os.path.join(self.LIST_SOUNDS_PATH, self.selected_snd_folder)

        self.list_of_images = [f for f in os.listdir(img_target) if os.path.isfile(os.path.join(img_target, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        self.list_of_sounds = [f for f in os.listdir(snd_target) if os.path.isfile(os.path.join(snd_target, f)) and f.lower().endswith(('.mp3', '.wav', '.ogg'))]
        
        if self.current_image_index >= len(self.list_of_images):
            self.current_image_index = 0

    def open_system_folder(self, path):
        """Ouvre le dossier spécifié directement dans l'explorateur Windows"""
        try:
            if os.name == 'nt':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
        except Exception as e:
            print(f"Erreur lors de l'ouverture du dossier : {e}")

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=6)
        self.grid_rowconfigure(0, weight=1)

        # ================= PANNEAU GAUCHE (STATUT / VISUEL) =================
        self.left_frame = ctk.CTkFrame(self, corner_radius=12)
        self.left_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        # FIX : Largeur fixe (width) et police monospace (Consolas) pour empêcher le UI de bouger
        self.label_minute = ctk.CTkLabel(
            self.left_frame, 
            text="--", 
            font=ctk.CTkFont(family="Consolas", size=22, weight="bold"),
            width=250 
        )
        self.label_minute.pack(pady=(15, 5))
        self.label_minute.pack_propagate(False)

        self.image_button = ctk.CTkButton(self.left_frame, text="", fg_color="transparent", hover_color="#2b2b2b", command=self.change_background_image)
        self.image_button.pack(expand=True, fill="both", padx=15, pady=5)

        self.lbl_folder_img = ctk.CTkLabel(self.left_frame, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_folder_img.pack(pady=(5, 0))
        self.menu_folder_img = ctk.CTkOptionMenu(self.left_frame, values=self.img_subfolders, command=self.on_img_folder_change)
        self.menu_folder_img.pack(pady=(0, 10), padx=20, fill="x")

        self.btn_add_image = ctk.CTkButton(self.left_frame, fg_color="#3a3a3a", hover_color="#505050", command=self.add_image_file)
        self.btn_add_image.pack(pady=(0, 10), padx=20, fill="x")
        
        self.label_boss_info = ctk.CTkLabel(self.left_frame, font=ctk.CTkFont(size=11), text_color="gray")
        self.label_boss_info.pack(pady=(0, 10))

        # ================= PANNEAU DROIT (ONGLETS) =================
        self.tabview = ctk.CTkTabview(self, corner_radius=12)
        self.tabview.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")

        self.tab_audio = self.tabview.add("Audio")
        self.tab_pranks = self.tabview.add("Pranks")
        self.tab_settings = self.tabview.add("Settings")
        self.tab_help = self.tabview.add("Help")

        # --- ONGLET 1: AUDIO & MINUTEUR ---
        self.label_min_val = ctk.CTkLabel(self.tab_audio, text="")
        self.label_min_val.pack(anchor="w", padx=20, pady=(5, 0))
        self.slider_min = ctk.CTkSlider(self.tab_audio, from_=0, to=60, number_of_steps=60, command=self.update_slider_labels)
        self.slider_min.set(1)
        self.slider_min.pack(fill="x", padx=20, pady=(0, 10))

        self.label_max_val = ctk.CTkLabel(self.tab_audio, text="")
        self.label_max_val.pack(anchor="w", padx=20)
        self.slider_max = ctk.CTkSlider(self.tab_audio, from_=0, to=60, number_of_steps=60, command=self.update_slider_labels)
        self.slider_max.set(8)
        self.slider_max.pack(fill="x", padx=20, pady=(0, 10))

        self.label_volume = ctk.CTkLabel(self.tab_audio, text="")
        self.label_volume.pack(anchor="w", padx=20)
        self.slider_volume = ctk.CTkSlider(self.tab_audio, from_=0.0, to=1.0, command=self.change_volume)
        self.slider_volume.set(0.7)
        self.slider_volume.pack(fill="x", padx=20, pady=(0, 15))

        self.lbl_folder_snd = ctk.CTkLabel(self.tab_audio, text="", anchor="w")
        self.lbl_folder_snd.pack(anchor="w", padx=20)
        self.menu_folder_snd = ctk.CTkOptionMenu(self.tab_audio, values=self.snd_subfolders, command=self.on_snd_folder_change)
        self.menu_folder_snd.pack(pady=(0, 15), padx=20, fill="x")

        self.btn_recalc = ctk.CTkButton(self.tab_audio, fg_color="#1f538d", hover_color="#153b66", command=self.manual_recalculate)
        self.btn_recalc.pack(fill="x", padx=40, pady=4)

        self.btn_add_sound = ctk.CTkButton(self.tab_audio, fg_color="#3a3a3a", hover_color="#505050", command=self.add_sound_file)
        self.btn_add_sound.pack(fill="x", padx=40, pady=4)

        self.btn_play_random = ctk.CTkButton(self.tab_audio, font=ctk.CTkFont(weight="bold"), fg_color="#2b7b51", hover_color="#1e5c3b", command=self.play_random_sound)
        self.btn_play_random.pack(fill="x", padx=40, pady=(4, 10))

        # --- ONGLET 2: FARCES & MEMES ---
        self.frame_meme = ctk.CTkFrame(self.tab_pranks, fg_color="transparent")
        self.frame_meme.pack(fill="x", padx=10, pady=5)
        self.switch_flash = ctk.CTkSwitch(self.frame_meme, text="")
        self.switch_flash.pack(side="left", padx=5)
        self.btn_preview_meme = ctk.CTkButton(self.frame_meme, width=120, fg_color="#8b0000", hover_color="#600000", command=self.run_subliminal_flash)
        self.btn_preview_meme.pack(side="right", padx=5)

        self.entry_flash_text = ctk.CTkEntry(self.tab_pranks, placeholder_text="YOU DIED")
        self.entry_flash_text.insert(0, "YOU DIED")
        self.entry_flash_text.pack(fill="x", padx=20, pady=5)
        
        self.label_flash_dur = ctk.CTkLabel(self.tab_pranks, text="")
        self.label_flash_dur.pack(anchor="w", padx=20)
        self.slider_flash_dur = ctk.CTkSlider(self.tab_pranks, from_=0.1, to=5.0, number_of_steps=49, command=self.update_flash_dur_label)
        self.slider_flash_dur.set(1.5)
        self.slider_flash_dur.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(self.tab_pranks, text="------------------------------------------------------------", text_color="gray").pack()

        self.frame_err = ctk.CTkFrame(self.tab_pranks, fg_color="transparent")
        self.frame_err.pack(fill="x", padx=10, pady=5)
        self.switch_popup = ctk.CTkSwitch(self.frame_err, text="")
        self.switch_popup.pack(side="left", padx=5)
        self.btn_preview_err = ctk.CTkButton(self.frame_err, width=120, fg_color="#3a3a3a", command=self.trigger_custom_popup)
        self.btn_preview_err.pack(side="right", padx=5)

        self.entry_popup_text = ctk.CTkEntry(self.tab_pranks)
        self.entry_popup_text.insert(0, "Alerte : Activité suspecte détectée.")
        self.entry_popup_text.pack(fill="x", padx=20, pady=(5, 10))

        # --- ONGLET 3: RÉGLAGES ---
        self.switch_mute = ctk.CTkSwitch(self.tab_settings, text="")
        self.switch_mute.pack(anchor="w", padx=20, pady=8)

        self.switch_win_err_sound = ctk.CTkSwitch(self.tab_settings, text="")
        self.switch_win_err_sound.pack(anchor="w", padx=20, pady=8)

        self.switch_chat_notif = ctk.CTkSwitch(self.tab_settings, text="")
        self.switch_chat_notif.pack(anchor="w", padx=20, pady=8)

        self.switch_chaos = ctk.CTkSwitch(self.tab_settings, text_color="coral")
        self.switch_chaos.pack(anchor="w", padx=20, pady=8)

        self.switch_stealth = ctk.CTkSwitch(self.tab_settings, command=self.toggle_camouflage)
        self.switch_stealth.pack(anchor="w", padx=20, pady=8)

        self.btn_lang = ctk.CTkButton(self.tab_settings, fg_color="#1f538d", command=self.toggle_language)
        self.btn_lang.pack(anchor="w", padx=20, pady=20)

        # --- ONGLET 4: AIDE & DOSSIERS ---
        self.frame_help_btns = ctk.CTkFrame(self.tab_help, fg_color="transparent")
        self.frame_help_btns.pack(fill="x", padx=10, pady=(10, 5))
        
        self.btn_open_img = ctk.CTkButton(self.frame_help_btns, command=lambda: self.open_system_folder(self.LIST_IMAGES_PATH))
        self.btn_open_img.pack(side="left", expand=True, padx=5)
        
        self.btn_open_snd = ctk.CTkButton(self.frame_help_btns, command=lambda: self.open_system_folder(self.LIST_SOUNDS_PATH))
        self.btn_open_snd.pack(side="right", expand=True, padx=5)

        self.textbox_help = ctk.CTkTextbox(self.tab_help, wrap="word", corner_radius=8)
        self.textbox_help.pack(fill="both", expand=True, padx=10, pady=10)

        self.update_image_display()

    # ================= GESTION DES DOSSIERS / SELECTION =================
    def on_img_folder_change(self, choice):
        self.selected_img_folder = choice
        self.refresh_directories()
        self.update_image_display()

    def on_snd_folder_change(self, choice):
        self.selected_snd_folder = choice
        self.refresh_directories()

    def update_dropdown_menus(self):
        self.menu_folder_img.configure(values=self.img_subfolders)
        self.menu_folder_img.set(self.selected_img_folder)
        self.menu_folder_snd.configure(values=self.snd_subfolders)
        self.menu_folder_snd.set(self.selected_snd_folder)

    # ================= LANGUE ET TRADUCTION =================
    def toggle_language(self):
        self.lang = "en" if self.lang == "fr" else "fr"
        self.update_language()

    def update_language(self):
        t = self.texts[self.lang]
        self.title(t["stealth_title"] if self.switch_stealth.get() else t["title"])
        
        self.tabview._segmented_button._buttons_dict["Audio"].configure(text=t["tab_audio"])
        self.tabview._segmented_button._buttons_dict["Pranks"].configure(text=t["tab_pranks"])
        self.tabview._segmented_button._buttons_dict["Settings"].configure(text=t["tab_settings"])
        self.tabview._segmented_button._buttons_dict["Help"].configure(text=t["tab_help"])
        
        self.btn_add_image.configure(text=t["add_img"])
        self.label_boss_info.configure(text=t["boss_key"])
        self.btn_add_sound.configure(text=t["add_sound"])
        self.btn_play_random.configure(text=t["play_test"])
        self.btn_recalc.configure(text=t["btn_recalc"])
        
        self.switch_chaos.configure(text=t["chaos"])
        self.switch_stealth.configure(text=t["stealth"])
        self.switch_flash.configure(text=t["meme_switch"])
        self.switch_popup.configure(text=t["err_switch"])
        self.switch_mute.configure(text=t["switch_mute"])
        self.switch_win_err_sound.configure(text=t["switch_win_err"])
        self.switch_chat_notif.configure(text=t["switch_chat_notif"])
        
        self.lbl_folder_img.configure(text=t["folder_img"])
        self.lbl_folder_snd.configure(text=t["folder_snd"])
        
        self.btn_preview_meme.configure(text=t["btn_preview"])
        self.btn_preview_err.configure(text=t["btn_preview"])
        self.btn_lang.configure(text=t["lang_switch"])
        
        self.btn_open_img.configure(text=t["btn_open_img_dir"])
        self.btn_open_snd.configure(text=t["btn_open_snd_dir"])
        
        self.textbox_help.configure(state="normal")
        self.textbox_help.delete("1.0", "end")
        self.textbox_help.insert("1.0", t["help_text"])
        self.textbox_help.configure(state="disabled")
        
        if not self.list_of_images: self.image_button.configure(text=t["no_img"])
        self.update_slider_labels()
        self.change_volume(self.slider_volume.get())
        self.update_flash_dur_label(self.slider_flash_dur.get())

    # ================= LOGIQUE DES MENUS INTERFACES =================
    def update_flash_dur_label(self, value):
        self.label_flash_dur.configure(text=self.texts[self.lang]["meme_dur"].format(float(value)))

    def update_slider_labels(self, _=None):
        val_min = int(self.slider_min.get())
        val_max = int(self.slider_max.get())
        if val_min > val_max:
            self.slider_max.set(val_min)
            val_max = val_min
        self.label_min_val.configure(text=self.texts[self.lang]["min_time"].format(val_min))
        self.label_max_val.configure(text=self.texts[self.lang]["max_time"].format(val_max))

    def change_volume(self, value):
        pygame.mixer.music.set_volume(float(value))
        self.label_volume.configure(text=self.texts[self.lang]["vol"].format(int(float(value) * 100)))

    def manual_recalculate(self):
        self.schedule_next_sound()

    # ================= GESTION DES FICHIERS & ANIMATION MAIN UI =================
    def add_image_file(self):
        files = filedialog.askopenfilenames(filetypes=[("Images & GIFs", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if files:
            target_dir = self.LIST_IMAGES_PATH if self.selected_img_folder == "/" else os.path.join(self.LIST_IMAGES_PATH, self.selected_img_folder)
            for file_path in files:
                shutil.copy(file_path, os.path.join(target_dir, os.path.basename(file_path)))
            self.refresh_directories()
            self.update_dropdown_menus()
            self.update_image_display()

    def add_sound_file(self):
        files = filedialog.askopenfilenames(filetypes=[("Audio", "*.mp3 *.wav *.ogg")])
        if files:
            target_dir = self.LIST_SOUNDS_PATH if self.selected_snd_folder == "/" else os.path.join(self.LIST_SOUNDS_PATH, self.selected_snd_folder)
            for file_path in files:
                shutil.copy(file_path, os.path.join(target_dir, os.path.basename(file_path)))
            self.refresh_directories()
            self.update_dropdown_menus()

    def stop_main_gif(self):
        if self.main_anim_id is not None:
            self.after_cancel(self.main_anim_id)
            self.main_anim_id = None

    def animate_main_gif(self, index):
        if not self.main_gif_frames or not self.list_of_images: return
        if index >= len(self.main_gif_frames): index = 0
        self.image_button.configure(image=self.main_gif_frames[index])
        self.main_anim_id = self.after(self.main_gif_delay, self.animate_main_gif, (index + 1) % len(self.main_gif_frames))

    def update_image_display(self):
        self.stop_main_gif()
        if not self.list_of_images:
            self.image_button.configure(image="", text=self.texts[self.lang]["no_img"])
            return
        try:
            img_folder = self.LIST_IMAGES_PATH if self.selected_img_folder == "/" else os.path.join(self.LIST_IMAGES_PATH, self.selected_img_folder)
            img_path = os.path.join(img_folder, self.list_of_images[self.current_image_index])
            img = Image.open(img_path)
            
            if getattr(img, "is_animated", False):
                self.main_gif_frames = []
                for frame in ImageSequence.Iterator(img):
                    f_rgba = frame.convert("RGBA")
                    ctk_img = ctk.CTkImage(light_image=f_rgba, dark_image=f_rgba, size=(220, 220))
                    self.main_gif_frames.append(ctk_img)
                self.main_gif_delay = img.info.get('duration', 100)
                self.image_button.configure(text="")
                self.animate_main_gif(0)
            else:
                ctk_img = ctk.CTkImage(light_image=img.convert("RGBA"), dark_image=img.convert("RGBA"), size=(220, 220))
                self.image_button.configure(image=ctk_img, text="")
        except Exception as e:
            print(f"Erreur image display: {e}")

    def change_background_image(self):
        if not self.list_of_images: return
        self.current_image_index = (self.current_image_index + 1) % len(self.list_of_images)
        self.update_image_display()

    # ================= SYSTEME DES COUPS EN LOUPES (PRANKS) =================
    def toggle_camouflage(self):
        t = self.texts[self.lang]
        if self.switch_stealth.get() == 1:
            self.title(t["stealth_title"])
            if self.tray_icon: self.tray_icon.title = "Windows Sync Host"
        else:
            self.title(t["title"])
            if self.tray_icon: self.tray_icon.title = t["title"]

    def boss_key_trigger(self):
        self.withdraw()
        self.switch_stealth.select()
        self.toggle_camouflage()

    def trigger_custom_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title(self.texts[self.lang]["popup_title"])
        popup.geometry("400x150")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)
        
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - 200
        y = (popup.winfo_screenheight() // 2) - 75
        popup.geometry(f"+{x}+{y}")

        label = ctk.CTkLabel(popup, text=self.entry_popup_text.get(), font=ctk.CTkFont(size=14), wraplength=350)
        label.pack(expand=True, padx=20, pady=20)
        ctk.CTkButton(popup, text=self.texts[self.lang]["btn_ok"], width=100, command=popup.destroy).pack(pady=(0, 15))

    def run_subliminal_flash(self):
        if not self.list_of_images: return
        flash_win = tk.Toplevel(self)
        flash_win.overrideredirect(True) 
        flash_win.attributes("-topmost", True)
        flash_win.configure(bg="black")

        lbl_img = tk.Label(flash_win, bg="black")
        lbl_img.pack(expand=True, fill="both", padx=15, pady=(15, 0))

        meme_text = self.entry_flash_text.get()
        if meme_text:
            lbl_txt = tk.Label(flash_win, text=meme_text, fg="#c8102e", bg="black", font=("Impact", 45))
            lbl_txt.pack(pady=(0, 15))

        try:
            img_folder = self.LIST_IMAGES_PATH if self.selected_img_folder == "/" else os.path.join(self.LIST_IMAGES_PATH, self.selected_img_folder)
            img_path = os.path.join(img_folder, self.list_of_images[self.current_image_index])
            img = Image.open(img_path)
            max_size = (600, 600)
            if getattr(img, "is_animated", False):
                frames = []
                for frame in ImageSequence.Iterator(img):
                    f_rgba = frame.convert("RGBA")
                    f_rgba.thumbnail(max_size, Image.Resampling.LANCZOS)
                    frames.append(ImageTk.PhotoImage(f_rgba))
                delay = img.info.get('duration', 100)
                def update_frame(index):
                    if not flash_win.winfo_exists(): return
                    lbl_img.configure(image=frames[index])
                    flash_win.after(delay, update_frame, (index + 1) % len(frames))
                update_frame(0)
                w, h = frames[0].width(), frames[0].height()
            else:
                img_rgba = img.convert("RGBA")
                img_rgba.thumbnail(max_size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img_rgba)
                lbl_img.configure(image=photo)
                lbl_img.image = photo 
                w, h = photo.width(), photo.height()

            x = (self.winfo_screenwidth() // 2) - (w // 2)
            y = (self.winfo_screenheight() // 2) - ((h + 80) // 2)
            flash_win.geometry(f"+{x}+{y}")
        except Exception as e:
            print(f"Erreur d'affichage flash: {e}")

        duration_ms = int(self.slider_flash_dur.get() * 1000)
        self.after(duration_ms, flash_win.destroy)

    # ================= GESTION AUDIO AVANCÉE =================
    def play_random_sound(self):
        if self.switch_mute.get() == 1:
            return

        def _play():
            try:
                if self.switch_win_err_sound.get() == 1:
                    if winsound:
                        winsound.MessageBeep(winsound.MB_ICONHAND)
                    return
                
                if self.switch_chat_notif.get() == 1 and not self.list_of_sounds:
                    if winsound:
                        winsound.Beep(1200, 150)
                        winsound.Beep(1800, 150)
                    return

                if self.list_of_sounds:
                    sound_folder = self.LIST_SOUNDS_PATH if self.selected_snd_folder == "/" else os.path.join(self.LIST_SOUNDS_PATH, self.selected_snd_folder)
                    sound_file = random.choice(self.list_of_sounds)
                    pygame.mixer.music.load(os.path.join(sound_folder, sound_file))
                    pygame.mixer.music.play()
            except Exception as e:
                print(f"Erreur audio: {e}")

        threading.Thread(target=_play, daemon=True).start()

    def schedule_next_sound(self):
        min_val = int(self.slider_min.get())
        max_val = int(self.slider_max.get())
        if self.switch_chaos.get() == 1:
            min_val = max(0, int(min_val * self.chaos_factor))
            max_val = max(1, int(max_val * self.chaos_factor))
            self.chaos_factor *= 0.75 
        else:
            self.chaos_factor = 1.0 

        rand_minutes = random.randint(min_val, max_val)
        self.next_play_time = datetime.now() + timedelta(minutes=rand_minutes)

    def sound_director_loop(self):
        now = datetime.now()
        
        if now >= self.next_play_time:
            self.play_random_sound()
            if self.switch_flash.get() == 1: self.run_subliminal_flash()
            if self.switch_popup.get() == 1: self.trigger_custom_popup()
            self.schedule_next_sound()

        time_diff = self.next_play_time - now
        total_sec = max(0, int(time_diff.total_seconds()))
        minutes_left = total_sec // 60
        seconds_left = total_sec % 60

        self.label_minute.configure(text=self.texts[self.lang]["next_event"].format(minutes_left, seconds_left))
        self.after(1000, self.sound_director_loop)

    # ================= BARRE DES TÂCHES =================
    def setup_system_tray(self):
        try:
            if self.list_of_images:
                img_folder = self.LIST_IMAGES_PATH if self.selected_img_folder == "/" else os.path.join(self.LIST_IMAGES_PATH, self.selected_img_folder)
                icon_img = Image.open(os.path.join(img_folder, self.list_of_images[0]))
            else:
                icon_img = Image.new('RGB', (64, 64), color='#FF4500')
        except:
            icon_img = Image.new('RGB', (64, 64), color='#FF4500')

        menu = pystray.Menu(
            pystray.MenuItem('Afficher', self.show_window),
            pystray.MenuItem('Quitter proprement', lambda: self.after(0, self.quit_application))
        )
        self.tray_icon = pystray.Icon("SoundMaker", icon_img, "SoundMaker Pro", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def minimize_to_tray(self):
        self.withdraw()

    def show_window(self):
        self.deiconify()

    def quit_application(self):
        if self.tray_icon: self.tray_icon.stop()
        pygame.mixer.quit()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = SoundMakerApp()
    app.mainloop()