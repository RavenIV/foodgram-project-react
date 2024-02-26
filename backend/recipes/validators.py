from django.core.validators import RegexValidator

from .constants import USERNAME_REGEX


class UsernameValidator(RegexValidator):
    regex = USERNAME_REGEX


class ColorValidator(RegexValidator):
    regex = r'^#([a-fA-F0-9]{6})$'
    message = 'Укажите цвет в hex-формате вида #123ABC'
