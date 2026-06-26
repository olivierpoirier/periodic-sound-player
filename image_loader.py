from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QImage, QPixmap


def load_qimage(path: Path) -> QImage:
    """Load regular Qt formats first, then use Pillow for AVIF-compatible decoding."""
    image = QImage(str(path))
    if not image.isNull():
        return image
    try:
        import pillow_avif  # noqa: F401 - registers the AVIF decoder with Pillow
        from PIL import Image

        with Image.open(path) as source:
            image = source.convert("RGBA")
            qimage = QImage(
                image.tobytes("raw", "RGBA"),
                image.width,
                image.height,
                image.width * 4,
                QImage.Format.Format_RGBA8888,
            ).copy()
        return qimage
    except (ImportError, OSError, ValueError):
        return QImage()


def load_pixmap(path: Path) -> QPixmap:
    pixmap = QPixmap(str(path))
    if not pixmap.isNull():
        return pixmap
    image = load_qimage(path)
    return QPixmap.fromImage(image) if not image.isNull() else QPixmap()
