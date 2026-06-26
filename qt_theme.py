from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor


@dataclass(frozen=True)
class ThemePalette:
    base: QColor
    surface: QColor
    surface_alt: QColor
    accent: QColor
    accent_alt: QColor
    text: QColor
    muted: QColor
    mode_accents: dict[str, QColor]

    @staticmethod
    def rgba(color: QColor, alpha: int = 255) -> str:
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})"

    @staticmethod
    def hex(color: QColor) -> str:
        return color.name()


THEME_CREDITS = {
    "pexels-david-kanigan-239927285-14027356.jpg": ("David Kanigan", "https://www.pexels.com/fr-fr/@david-kanigan-239927285/"),
    "pexels-vizi-kata-373820-36419543.jpg": ("Vizi Kata", "https://www.pexels.com/fr-fr/@vizi-kata-373820/"),
    "pexels-jordicosta-32167957.jpg": ("Jordi Costa", "https://www.pexels.com/fr-fr/@jordicosta/"),
    "pexels-darya-grey_owl-132130036-12753143.jpg": ("Darya Grey Owl", "https://www.pexels.com/fr-fr/@darya-grey_owl-132130036/"),
    "pexels-photo-5226950.avif": ("Samuel Butikofer", "https://www.pexels.com/fr-fr/@samuel-butikofer-3490375/"),
    "pexels-photo-4195781.avif": ("Nico Kalka", "https://www.pexels.com/fr-fr/@nico-kalka-2173551/"),
    "pexels-photo-37161600.avif": ("幼聪 戴", "https://www.pexels.com/fr-fr/@2149938750/"),
    "pexels-photo-5502610.avif": ("Mike van Schoonderwalt", "https://www.pexels.com/fr-fr/@mike-van-schoonderwalt-1884800/"),
}

HOME_THEME_CAPTIONS = {
    "43bda22b-82ef-4b3c-a794-2e820dc50ba6.jpg": {
        "fr": "Maison · Aghate est venue ici d'elle-même",
        "en": "Home · Aghate came here on her own",
    },
    "169ebf2d-89b3-4579-a171-f6b27542402b.jpg": {"fr": "Maison · Albert", "en": "Home · Albert"},
    "4925f338-4956-465d-8115-60e8b0d2387c.jpg": {"fr": "Maison · Édouard", "en": "Home · Édouard"},
    "31728c8e-c463-42b1-817e-82e889524139.jpg": {"fr": "Maison · Violette", "en": "Home · Violette"},
    "a46828ae-e352-4d5e-9de2-89c3e3b04a0a.jpg": {"fr": "Maison · Aghate", "en": "Home · Aghate"},
    "fb980b8b-5f52-41ed-94cc-120179643646.jpg": {"fr": "Maison · Violette", "en": "Home · Violette"},
}

BUILTIN_THEME_NAMES = frozenset(THEME_CREDITS) | frozenset(HOME_THEME_CAPTIONS)


def build_theme_qss(palette: ThemePalette) -> str:
    """Build the complete UI skin from the active background palette."""
    rgba = palette.rgba
    hex_color = palette.hex
    return f"""
    QWidget {{ background: transparent; color: {hex_color(palette.text)}; font-family: Segoe UI; font-size: 13px; }}
    QLabel {{ background: transparent; }}
    #header {{ background: {rgba(palette.base, 132)}; border-bottom: 2px solid {rgba(palette.accent_alt, 88)}; }}
    #brandMark {{ background: transparent; border: 0; padding: 0; }}
    #photoCreditBar {{ background: {rgba(palette.base, 92)}; border-top: 2px solid {rgba(palette.text, 44)}; }}
    #photoCredit {{ color: {hex_color(palette.muted)}; font-size: 11px; padding: 2px 0; }}
    #photoCredit a {{ color: {hex_color(palette.text)}; text-decoration: underline; }}
    #panel, #settingsShell, QGroupBox#section {{ background: transparent; border: 0; }}
    #settingsShell {{ background: transparent; }}
    #tabSurface {{ background: transparent; border: 0; }}
    #modeTabs::pane, #modeTabs {{ background: transparent; border: 0; }}
    #modeTabs::pane {{ margin-top: 4px; }}
    #modeTabs QTabBar {{ background: transparent; border: 0; padding: 0; }}
    #modeTabs QTabBar::tab {{ background: transparent; border: 0; color: {hex_color(palette.muted)}; min-width: 62px; padding: 6px 12px; margin-right: 6px; }}
    #modeTabs QTabBar::tab:selected {{ color: {hex_color(palette.text)}; }}
    QGroupBox#section {{ margin-top: 11px; font-weight: 700; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 16px; padding: 0 8px; color: {hex_color(palette.text)}; background: {rgba(palette.base, 96)}; }}
    #timerCard {{ background: transparent; border: 0; }}
    #previewCard, #imagePreview {{ background: {rgba(palette.base, 108)}; border: 2px solid {rgba(palette.text, 108)}; border-radius: 15px; color: {hex_color(palette.muted)}; }}
    #appTitle, #timerText {{ color: {hex_color(palette.text)}; font-weight: 800; }}
    #appTitle {{ font-size: 23px; }} #timerText {{ font-family: Consolas; font-size: 23px; }}
    #settingsTitle {{ font-size: 18px; font-weight: 800; }} #fieldTitle {{ color: {hex_color(palette.text)}; font-size: 14px; font-weight: 700; }}
    #muted, QLabel#muted {{ color: {hex_color(palette.muted)}; }} #tinyMuted {{ color: {rgba(palette.muted, 188)}; font-size: 12px; }}
    #sectionKicker {{ color: {hex_color(palette.accent)}; font-size: 11px; font-weight: 900; }}
    #filePill {{ color: {hex_color(palette.text)}; background: {rgba(palette.surface_alt, 80)}; border: 2px solid {rgba(palette.text, 108)}; border-radius: 10px; padding: 7px 11px; }}
    #modeCard {{ background: transparent; border: 0; min-height: 68px; }}
    #modeCard:hover {{ background: transparent; }}
    QFrame#modeCard[active=\"true\"] {{ background: transparent; border: 0; }}
    QPushButton {{ background: {rgba(palette.surface_alt, 108)}; border: 2px solid {rgba(palette.text, 96)}; border-radius: 10px; padding: 9px 15px; color: {hex_color(palette.text)}; font-weight: 650; }}
    QPushButton:hover {{ background: {rgba(palette.accent_alt, 122)}; border-color: {rgba(palette.accent, 146)}; }} QPushButton:pressed {{ background: {rgba(palette.base, 128)}; }}
    QPushButton#ghostButton {{ background: {rgba(palette.text, 18)}; border: 2px solid {rgba(palette.text, 78)}; }}
    QPushButton#secondaryButton {{ background: {rgba(palette.surface, 88)}; }} QPushButton#warningButton {{ background: {rgba(palette.accent, 116)}; border-color: {rgba(palette.text, 76)}; }}
    QPushButton#successButton, QPushButton#timerButton, QPushButton#helpButton, QPushButton#coffeeButton {{ background: transparent; border: 0; }}
    QPushButton#dangerButton {{ background: {rgba(palette.surface_alt, 102)}; }}
    QPushButton#dockToggle {{ color: {hex_color(palette.text)}; background: {rgba(palette.base, 104)}; border: 2px solid {rgba(palette.text, 92)}; border-radius: 14px; padding: 8px 6px; font-size: 18px; font-weight: 800; text-align: right; }} QPushButton#dockToggle:hover {{ background: {rgba(palette.accent_alt, 122)}; border-color: {rgba(palette.accent, 148)}; }}
    QComboBox, QLineEdit {{ background: {rgba(palette.base, 120)}; border: 2px solid {rgba(palette.text, 116)}; border-radius: 10px; padding: 8px 11px; selection-background-color: {hex_color(palette.accent_alt)}; }}
    QComboBox:hover, QLineEdit:hover {{ border-color: {rgba(palette.accent, 150)}; }}
    QComboBox:focus, QLineEdit:focus {{ border-color: {rgba(palette.accent, 188)}; background: {rgba(palette.surface, 134)}; }}
    QComboBox#gardenSelect, QLineEdit#gardenInput {{ background: {rgba(palette.surface, 128)}; border-color: {rgba(palette.text, 122)}; border-radius: 11px; min-height: 24px; padding: 8px 12px; }}
    QComboBox#gardenSelect::drop-down {{ width: 30px; border: 0; border-left: 2px solid {rgba(palette.text, 86)}; background: {rgba(palette.accent, 22)}; }}
    QAbstractItemView, QMenu {{ background: {rgba(palette.base, 136)}; border: 2px solid {rgba(palette.text, 116)}; border-radius: 9px; color: {hex_color(palette.text)}; }}
    QAbstractItemView::item:hover, QMenu::item:selected {{ background: {rgba(palette.accent_alt, 124)}; }} QMenu::item {{ padding: 7px 24px 7px 10px; border-radius: 8px; }}
    #settingsTabScroll, #modesScroll {{ background: {rgba(palette.base, 14)}; }}
    QScrollBar:vertical {{ background: {rgba(palette.base, 62)}; width: 10px; margin: 8px 3px 8px 2px; border: 0; border-radius: 5px; }}
    QScrollBar::handle:vertical {{ background: {rgba(palette.accent_alt, 130)}; min-height: 42px; border: 2px solid {rgba(palette.text, 92)}; border-radius: 5px; }} QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QSlider {{ min-height: 24px; padding: 0 10px; }} QSlider::groove:horizontal {{ height: 6px; background: {rgba(palette.muted, 96)}; border: 2px solid {rgba(palette.text, 58)}; border-radius: 3px; }}
    QSlider::sub-page:horizontal {{ background: {hex_color(palette.accent_alt)}; border-radius: 3px; }} QSlider::handle:horizontal {{ background: {hex_color(palette.accent)}; width: 19px; margin: -8px 0; border-radius: 10px; border: 2px solid {rgba(palette.text, 168)}; }}
    QRadioButton, QCheckBox {{ color: {hex_color(palette.text)}; font-size: 14px; font-weight: 700; spacing: 8px; }}
    """
