import re

from django.core.exceptions import ValidationError


def validate_username(username):
    if not re.fullmatch(r'^[\w.@+-]+\z', username):
        raise ValidationError(
            'Имя пользователя должно содержать только латинские буквы, '
            'цифры и символы @/./+/-/_'
        )


def validate_color(color):
    if not re.fullmatch(r'^#([a-fA-F0-9]{6})$', color):
        raise ValidationError(
            'Укажите цвет в hex-формате вида #123ABC'
        )
