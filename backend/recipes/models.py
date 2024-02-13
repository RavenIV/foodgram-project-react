from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

from .constants import MIN_COOKING_TIME


class User(AbstractUser):

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'пользователи'
        default_related_name = 'users'


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name='Пользователь'
    )
    subscribing = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Подписан на'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscribing'], name='unique_subscribers'
            ),
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'подписки'

    def __str__(self):
        return f'{self.user=} {self.subscribing=}'


class Tag(models.Model):
    name = models.CharField('Название', unique=True, max_length=200)
    color = models.CharField('Цвет', unique=True, max_length=7)
    slug = models.SlugField('Слаг', unique=True, max_length=200)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return f'{self.name=:.30}, {self.color=}, {self.slug=:.30}'


class Ingridient(models.Model):
    name = models.CharField('Название', max_length=200)
    measurement_unit = models.CharField('Единицы измерения', max_length=200)

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'ингридиенты'

    def __str__(self):
        return f'{self.name=:.30} {self.measurement_unit=:.30}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор'
    )
    name = models.CharField('Название', max_length=200)
    image = models.ImageField('Картинка', upload_to='recipes/images/')
    text = models.TextField('Описание')
    ingridients = models.ManyToManyField(
        Ingridient, through='RecipeIngridients', verbose_name='Ингридиенты'
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(MIN_COOKING_TIME),]
    )
    pub_date = models.DateTimeField(
        'Дата публикации', auto_now_add=True, db_index=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'рецепты'
        default_related_name = 'recipes'
        ordering = ['-pub_date']

    def __str__(self):
        return f'{self.name:.50}'


class RecipeIngridients(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingridient = models.ForeignKey(Ingridient, on_delete=models.PROTECT)
    amount = models.PositiveSmallIntegerField('Количество')

    def __str__(self):
        return f'{self.recipe} {self.ingridient} {self.amount}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorite_recipes'
    )
    favorite_recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='users_favorited'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'favorite_recipe'], name='unique_favorites'
            ),
        ]
    
    def __str__(self):
        return f'{self.user} {self.favorite_recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_cart'
    )
    shopping_recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='users_added_to_cart'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'shopping_recipe'],
                name='unique_shopping_recipes'
            ),
        ]

    def __str__(self):
        return f'{self.user} {self.shopping_recipe}'
