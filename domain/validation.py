"""Text checks shared by the entities."""

import re

from domain.exceptions import ValidationError

# Letters (with accents), spaces, dots, apostrophes and hyphens.
TEXT_PATTERN = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ .'\-]+$")


def clean_text(value, field, max_length, min_length=2):
    """Trim and collapse spaces, then check length and allowed characters."""
    text = " ".join(str(value or "").split())
    if not text:
        raise ValidationError(f"El {field} es obligatorio.")
    if len(text) < min_length:
        raise ValidationError(f"El {field} debe tener al menos {min_length} caracteres.")
    if len(text) > max_length:
        raise ValidationError(f"El {field} no puede superar los {max_length} caracteres.")
    if not TEXT_PATTERN.match(text):
        raise ValidationError(
            f"El {field} solo puede tener letras, espacios, puntos, apóstrofos y guiones."
        )
    return text
