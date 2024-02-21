from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

from .constants import MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT


class User(AbstractUser):
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    email = models.EmailField(unique=True, max_length=254)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'пользователи'
        default_related_name = 'users'
        ordering = ['username']

    def __str__(self):
        return f'id:{self.pk}, {self.username}'


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='subscribing'
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
        return (
            f'id:{self.pk}, '
            f'name:{self.name:.30}, '
            f'color:{self.color}, '
            f'slug:{self.slug:.30}'
        )


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=200)
    measurement_unit = models.CharField('Единицы измерения', max_length=200)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'ингредиенты'

    def __str__(self):
        return f'id:{self.pk}, {self.name:.30} ({self.measurement_unit:.30})'


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор'
    )
    name = models.CharField('Название', max_length=200)
    image = models.ImageField('Картинка', upload_to='recipes/images/')
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient, through='Meal', verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(MIN_COOKING_TIME)]
    )
    pub_date = models.DateTimeField(
        'Дата публикации', auto_now_add=True, db_index=True
    )
    favorited_by = models.ManyToManyField(
        User,
        blank=True,
        related_name='favorite_recipes',
        verbose_name='Добавили в избранное'
    )
    shopped_by = models.ManyToManyField(
        User,
        blank=True,
        related_name='shopping_recipes',
        verbose_name='Добавили в покупки'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'рецепты'
        default_related_name = 'recipes'
        ordering = ['-pub_date']

    def __str__(self):
        return f'id:{self.pk}, {self.name:.50}'


class Meal(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.PROTECT, verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество', validators=[MinValueValidator(MIN_INGREDIENT_AMOUNT),]
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'ингредиенты рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            ),
        ]

    def __str__(self):
        return f'{self.recipe}, {self.ingredient} {self.amount}'
