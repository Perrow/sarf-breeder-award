from io import BytesIO

from django.core.exceptions import ValidationError
from PIL import Image

EXPECTED_SIZE = (200, 250)


def _image_info(value):
    try:
        position = value.tell()
    except (AttributeError, OSError):
        position = None

    try:
        if hasattr(value, "seek"):
            value.seek(0)
        data = value.read()
    finally:
        if position is not None and hasattr(value, "seek"):
            value.seek(position)

    try:
        with Image.open(BytesIO(data)) as image:
            image.load()
            size = image.size
            image_format = image.format
            has_transparency = False
            if "A" in image.getbands():
                alpha = image.getchannel("A")
                extrema = alpha.getextrema()
                has_transparency = extrema is not None and extrema[0] < 255
            elif "transparency" in image.info:
                has_transparency = True
            return size, image_format, has_transparency
    except (OSError, ValueError) as exc:
        raise ValidationError("Filen är inte en giltig bild.") from exc


def validate_award_image_dimensions(value):
    size, _, _ = _image_info(value)
    if size != EXPECTED_SIZE:
        raise ValidationError("Bilden måste vara exakt 200 × 250 pixlar.")


def validate_achievement_overlay(value):
    size, image_format, has_transparency = _image_info(value)
    if size != EXPECTED_SIZE:
        raise ValidationError("Bilden måste vara exakt 200 × 250 pixlar.")
    if image_format != "PNG":
        raise ValidationError("Utmärkelsebilden måste vara en PNG-fil.")
    if not has_transparency:
        raise ValidationError("Utmärkelsebilden måste innehålla genomskinlighet.")
