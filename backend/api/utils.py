from datetime import datetime
from io import BytesIO

from recipes.models import User


def create_shopping_list(user: User) -> BytesIO:
    products = [
        f'{product.total_amount} {product.measurement_unit} - '
        f'{product.name}'
        for product in user.shopping_cart()
    ]
    recipes = ', '.join(
        [f'"{recipe.name}"' for recipe in user.shopping_recipes.all()]
    )
    today = datetime.now().strftime('%H:%M:%S %d.%m.%Y')
    shopping_list = (
        f'СПИСОК ПОКУПОК\n\n'
        f'Создан: {today}\n'
        f'Рецепты: {recipes}\n\n'
    )
    for index, line in enumerate(products, start=1):
        shopping_list += f'{index}. {line}\n'
    return BytesIO(shopping_list.encode('utf-8'))
