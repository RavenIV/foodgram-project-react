import re

from django.core.exceptions import ValidationError


def validate_username(username):
    if not re.fullmatch(r'^[\w.@+-]+\z', username):
        raise ValidationError(
            'Имя пользователя должно содержать только латинские буквы, '
            'цифры и символы @/./+/-/_'
        )
