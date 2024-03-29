from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

from . import constants
from .validators import ColorValidator, validate_username


class User(AbstractUser):

    username = models.CharField(
        'Ник',
        max_length=constants.MAX_USERNAME,
        unique=True,
        validators=[validate_username]
    )
    first_name = models.CharField('Имя', max_length=constants.MAX_FIRST_NAME)
    last_name = models.CharField('Фамилия', max_length=constants.MAX_LAST_NAME)
    email = models.EmailField(unique=True, max_length=constants.MAX_EMAIL)

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'пользователи'
        ordering = ('username',)

    def __repr__(self):
        return (
            f'<{type(self).__name__} '
            f'{self.pk=}, '
            f'{self.username=:.30}, '
            f'{self.email=:.30}, '
            f'{self.first_name=:.30}, '
            f'{self.last_name=:.30}>'
        )

    def __str__(self):
        return f'{self.username:.50}'

    def shopping_cart(self):
        return Ingredient.objects.filter(
            recipes__shopped_by=self
        ).annotate(total_amount=models.Sum('recipe_products__amount'))


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='subscribed_to'
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

    def __repr__(self):
        return f'<{type(self).__name__} {self.user=} {self.subscribing=}>'

    def __str__(self):
        return f'{self.user} подписан на {self.subscribing}'


class Tag(models.Model):
    name = models.CharField(
        'Название', unique=True, max_length=constants.MAX_TAG_NAME
    )
    color = models.CharField(
        'Код цвета',
        unique=True,
        max_length=constants.MAX_TAG_COLOR,
        validators=[ColorValidator()]
    )
    slug = models.SlugField(
        'Слаг', unique=True, max_length=constants.MAX_TAG_SLUG
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'теги'

    def __repr__(self):
        return (
            f'<{type(self).__name__} '
            f'{self.pk=}, '
            f'{self.name=:.30}, '
            f'{self.color=}, '
            f'{self.slug=:.30}>'
        )

    def __str__(self):
        return f'{self.name:.30}'


class Ingredient(models.Model):
    name = models.CharField(
        'Название', max_length=constants.MAX_INGREDIENT_NAME
    )
    measurement_unit = models.CharField(
        'Единица измерения', max_length=constants.MAX_INGREDIENT_MEASURE
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

    def __repr__(self):
        return (
            f'<{type(self).__name__} '
            f'{self.pk=} '
            f'{self.name=:.30} '
            f'{self.measurement_unit=:.30}>'
        )

    def __str__(self):
        return f'{self.name:.30} ({self.measurement_unit:.30})'


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор'
    )
    name = models.CharField('Название', max_length=constants.MAX_RECIPE_NAME)
    image = models.ImageField('Картинка', upload_to='recipes/images/')
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeProduct', verbose_name='Продукты'
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(constants.MIN_COOKING_TIME)]
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
        ordering = ('-pub_date',)

    def __repr__(self):
        return (
            f'<{type(self).__name__} '
            f'{self.pk=}, '
            f'{self.name=:.50}, '
            f'{self.author.username=}, '
            f'{self.text=:.30}, '
            f'{self.image=}, '
            f'{self.cooking_time=}, '
            f'{self.ingredients=}, '
            f'{self.tags=}, '
            f'{self.pub_date=}, '
            f'{self.favorited_by=}, '
            f'{self.shopped_by=}>'
        )

    def __str__(self):
        return f'{self.name:.50}'


class RecipeProduct(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.PROTECT, verbose_name='Продукт',
    )
    amount = models.PositiveSmallIntegerField(
        'Мера',
        validators=[MinValueValidator(constants.MIN_INGREDIENT_AMOUNT)]
    )

    class Meta:
        verbose_name = 'Продукт для рецепта'
        verbose_name_plural = 'продукты для рецепта'
        default_related_name = 'recipe_products'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            ),
        ]

    def __repr__(self):
        return (
            f'<{type(self).__name__} '
            f'{self.pk=} '
            f'{self.recipe=} '
            f'{self.ingredient=} '
            f'{self.amount=}>'
        )

    def __str__(self):
        return f'{self.recipe}: {self.ingredient} - {self.amount}'
