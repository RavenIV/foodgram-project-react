import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .constants import INVALID_USERNAMES


def validate_username(username):
    if username in INVALID_USERNAMES:
        raise ValidationError(f'Нельзя использовать {username} как username')
    invalid_symbols = re.findall(r'[^\w.@+-]', username)
    if invalid_symbols:
        raise ValidationError(
            f'Нельзя использовать символы {set(invalid_symbols)}'
        )
    return username


class ColorValidator(RegexValidator):
    regex = r'^#([a-fA-F0-9]{6})$'
    message = 'Укажите цвет в hex-формате вида #123ABC'
