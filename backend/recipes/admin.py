from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe

from .filters import CookingTimeListFilter, SubscriptionListFilter
from .models import Ingredient, RecipeProduct, Recipe, Subscription, Tag, User


class IngredientInline(admin.TabularInline):
    model = RecipeProduct
    extra = 0


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_filter = (
        'is_staff', 'is_superuser', 'is_active', SubscriptionListFilter
    )
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'recipes_count',
        'subscribed_to_count',
        'subscribers_count'
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            recipes_count=Count('recipes', distinct=True),
            subscribed_to_count=Count('subscribed_to', distinct=True),
            subscribers_count=Count('subscribers', distinct=True),
        )

    @admin.display(description='Рецепты', ordering='recipes_count')
    def recipes_count(self, user):
        return user.recipes_count

    @admin.display(description='Подписки', ordering='subscribed_to_count')
    def subscribed_to_count(self, user):
        return user.subscribed_to_count

    @admin.display(description='Подписчики', ordering='subscribers_count')
    def subscribers_count(self, user):
        return user.subscribers_count


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [IngredientInline]
    list_display = (
        'name',
        'author_link',
        'favorited_count',
        'cooking_time',
        'image_tag',
        'tags_display',
        'ingredients_display'
    )
    list_filter = ('author__username', 'tags__name', CookingTimeListFilter)
    search_fields = ['tags__name', 'name', 'author__username']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            favorited_count=Count('favorited_by', distinct=True),
        )

    @admin.display(description='Добавлено в избранное')
    def favorited_count(self, recipe):
        return recipe.favorited_count

    @admin.display(description='Автор', ordering='author__username')
    @mark_safe
    def author_link(self, recipe):
        return '<a href="{}">{}</a>'.format(
            reverse('admin:recipes_user_change', args=[recipe.author.id]),
            recipe.author.username
        )

    @admin.display(description='Картинка')
    @mark_safe
    def image_tag(self, recipe):
        return '<img src="{}" width="100px" height="100px" />'.format(
            recipe.image.url
        )

    @admin.display(description='Теги')
    @mark_safe
    def tags_display(self, recipe):
        return '<br>'.join([tag.name for tag in recipe.tags.all()])

    @admin.display(description='Продукты')
    @mark_safe
    def ingredients_display(self, recipe):
        return '<br>'.join([
            f'{product.ingredient.name} - '
            f'{product.amount} {product.ingredient.measurement_unit}'
            for product in recipe.recipe_products.all()
        ])


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipes_count')
    list_filter = ['measurement_unit']
    search_fields = ['name']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            recipes_count=Count('recipes', distinct=True),
        )

    @admin.display(description='Количество рецептов',
                   ordering='recipes_count')
    def recipes_count(self, ingredient):
        return ingredient.recipes_count


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color_display',
        'slug',
        'recipes_count'
    )

    def get_queryset(self, request):
        tags = super().get_queryset(request)
        return tags.annotate(
            recipes_count=Count('recipes', distinct=True),
        )

    @admin.display(description='Сколько раз применен',
                   ordering='recipes_count')
    def recipes_count(self, tag):
        return tag.recipes_count

    @admin.display(description='Цвет', ordering='color')
    @mark_safe
    def color_display(self, tag):
        return '<div style="background-color:{color}">{color}</div>'.format(
            color=tag.color
        )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscribing')


admin.site.unregister(Group)
admin.site.site_header = 'Foodgram Admin'
admin.site.site_title = 'Foodgram Admin Portal'
admin.site.index_title = (
    'Добро пожаловать на портал администратора Foodgram'
)
