from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from qt_widgets import GardenComboBox, GardenToggle, PaintedButton, SafeSlider, SmoothRadioButton


@dataclass(frozen=True)
class TabSpec:
    label: str
    description: str
    builder: Callable[[QVBoxLayout], None]


def label(text: str, object_name: str = "") -> QLabel:
    widget = QLabel(text)
    widget.setWordWrap(True)
    if object_name:
        widget.setObjectName(object_name)
    return widget


def add_tab(tabs: QTabWidget, spec: TabSpec) -> QVBoxLayout:
    scroll = QScrollArea()
    scroll.setObjectName("settingsTabScroll")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(8, 9, 8, 8)
    layout.setSpacing(7)
    if spec.description:
        layout.addWidget(label(spec.description, "muted"))
    spec.builder(layout)
    layout.addStretch(1)

    scroll.setWidget(page)
    tabs.addTab(scroll, spec.label)
    return layout


def add_responsive_row(layout: QVBoxLayout, widgets: list[QWidget], compact: bool, stretch_index: int | None = None) -> None:
    if compact:
        for widget in widgets:
            layout.addWidget(widget)
        return
    row = QHBoxLayout()
    for index, widget in enumerate(widgets):
        row.addWidget(widget, 1 if stretch_index == index else 0)
    layout.addLayout(row)


def add_button_row(layout: QVBoxLayout, buttons: list[QPushButton], compact: bool) -> None:
    add_responsive_row(layout, buttons, compact)


def add_labeled_widget_row(
    layout: QVBoxLayout,
    title: str,
    widget: QWidget,
    compact: bool,
    trailing: QWidget | None = None,
) -> None:
    widgets = [label(title, "fieldTitle"), widget]
    if trailing:
        widgets.append(trailing)
    add_responsive_row(layout, widgets, compact, stretch_index=1)


def add_radio_row(layout: QVBoxLayout, radios: list[QRadioButton], compact: bool) -> None:
    if compact:
        for radio in radios:
            layout.addWidget(radio)
        return
    row = QHBoxLayout()
    for radio in radios:
        row.addWidget(radio)
    row.addStretch(1)
    layout.addLayout(row)


def make_radio_group(options: list[tuple[str, bool, Callable[[bool], None]]]) -> list[QRadioButton]:
    radios = []
    for text, checked, callback in options:
        radio = SmoothRadioButton(text)
        radio.setChecked(checked)
        radio.toggled.connect(callback)
        radios.append(radio)
    return radios


def add_toggle_row(
    layout: QVBoxLayout,
    text: str,
    checked: bool,
    callback: Callable[[bool], None],
    no_text: str,
    yes_text: str,
) -> GardenToggle:
    row = QHBoxLayout()
    row.addWidget(label(text, "muted"))
    row.addStretch(1)
    row.addWidget(label(no_text, "muted"))
    toggle = GardenToggle()
    toggle.setChecked(checked)
    toggle.toggled.connect(callback)
    row.addWidget(toggle)
    row.addWidget(label(yes_text, "muted"))
    layout.addLayout(row)
    return toggle


def add_slider_grid(
    layout: QVBoxLayout,
    items: list[tuple[QLabel, SafeSlider]],
) -> None:
    grid = QGridLayout()
    grid.setHorizontalSpacing(14)
    grid.setVerticalSpacing(4)
    for column, (text_label, slider) in enumerate(items):
        grid.addWidget(text_label, 0, column)
        grid.addWidget(slider, 1, column)
    layout.addLayout(grid)


def make_slider(low: int, high: int, value: int, callback: Callable[[int], None]) -> SafeSlider:
    slider = SafeSlider(Qt.Horizontal)
    slider.setRange(low, high)
    slider.setValue(value)
    slider.valueChanged.connect(callback)
    return slider


def add_folder_picker(
    layout: QVBoxLayout,
    title: str,
    values: list[str],
    selected: str,
    on_change: Callable[[str], None],
    import_text: str,
    on_import: Callable[[], None],
    compact: bool,
) -> GardenComboBox:
    combo = GardenComboBox()
    combo.addItems(values)
    combo.setCurrentText(selected)
    combo.currentTextChanged.connect(on_change)
    import_button = PaintedButton(import_text)
    import_button.clicked.connect(on_import)
    add_labeled_widget_row(layout, title, combo, compact, import_button)
    return combo


def add_selected_file_controls(
    layout: QVBoxLayout,
    choose_text: str,
    empty_text: str,
    selected_path: Path | None,
    import_text: str,
    on_choose: Callable[[], None],
    on_import: Callable[[], None],
    compact: bool,
) -> QLabel:
    choose_button = PaintedButton(choose_text)
    choose_button.setObjectName("secondaryButton")
    choose_button.clicked.connect(on_choose)

    name_label = QLabel(selected_path.name if selected_path else empty_text)
    name_label.setObjectName("filePill")
    name_label.setMinimumWidth(0)
    name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    import_button = PaintedButton(import_text)
    import_button.clicked.connect(on_import)

    add_responsive_row(layout, [choose_button, name_label, import_button], compact, stretch_index=1)
    return name_label


def add_text_input_row(
    layout: QVBoxLayout,
    title: str,
    input_widget: QLineEdit,
    compact: bool,
) -> None:
    add_labeled_widget_row(layout, title, input_widget, compact)


def add_volume_controls(
    layout: QVBoxLayout,
    text: str,
    value: int,
    callback: Callable[[int], None],
) -> QLabel:
    text_label = label(text, "muted")
    slider = make_slider(0, 100, value, callback)
    row = QHBoxLayout()
    row.addWidget(text_label)
    row.addWidget(slider, 1)
    layout.addLayout(row)
    return text_label


def add_image_preview(
    layout: QVBoxLayout,
    placeholder: str,
    clickable_hint: str,
    on_click: Callable[[], None] | None,
    show_name: bool,
) -> tuple[QLabel, QLabel | None]:
    image_label = QLabel(placeholder)
    image_label.setObjectName("imagePreview")
    image_label.setAlignment(Qt.AlignCenter)
    image_label.setScaledContents(False)
    image_label.setFixedHeight(210)
    image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    if on_click:
        image_label.setToolTip(clickable_hint)
        image_label.mousePressEvent = lambda _event: on_click()
    layout.addWidget(image_label)

    name_label = None
    if show_name:
        name_label = QLabel(placeholder)
        name_label.setObjectName("filePill")
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setMinimumWidth(0)
        name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(name_label)
    return image_label, name_label
