from datetime import datetime
from typing import Union

from django.http import HttpRequest
from rest_framework.request import Request

from recipes.models import User
from .serializers import UserSerializer, RecipeReadSerializer


def create_shopping_list(user: User) -> str:
    return '\n'.join([
        'СПИСОК ПОКУПОК (от {})'.format(
            datetime.now().strftime('%H:%M:%S %d.%m.%Y')
        ),
        '',
        'Рецепты:\n{}'.format('\n'.join(
            [f'* {recipe.name}' for recipe in user.shopping_recipes.all()]
        )),
        '',
        'Продукты:\n{}'.format('\n'.join([
            f'{index}. {line}\n' for index, line in enumerate([
                f'{product.total_amount} {product.measurement_unit} - '
                f'{product.name}'
                for product in user.shopping_cart()
            ], start=1)
        ]))
    ])


def get_subscribing_data(subscribing: User,
                         request: Union[HttpRequest, Request]) -> dict:
    limit = int(request.GET.get('recipes_limit', 10**10))
    return dict(
        UserSerializer(subscribing, context={'request': request}).data,
        recipes=RecipeReadSerializer(
            subscribing.recipes.all()[:limit], many=True
        ).data,
        recipes_count=subscribing.recipes.count()
    )
