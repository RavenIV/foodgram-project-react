from datetime import datetime

from recipes.models import User


def create_shopping_list(user: User) -> str:
    return '\n'.join([
        'СПИСОК ПОКУПОК (от {})'.format(
            datetime.now().strftime('%H:%M:%S %d.%m.%Y')
        ),
        '',
        'Рецепты:',
        *[f'* {recipe.name}' for recipe in user.shopping_recipes.all()],
        '',
        'Продукты:',
        *[f'{index}. {line}' for index, line in enumerate(
            [
                f'{product.total_amount} {product.measurement_unit} - '
                f'{product.name}'for product in user.shopping_cart()
            ],
            start=1
        )]
    ])
