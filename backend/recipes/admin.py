from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe

from .filters import SubscriptionListFilter
from .models import Ingredient, Meal, Recipe, Subscription, Tag, User


class IngredientInline(admin.TabularInline):
    model = Meal
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

    @admin.display(description='Рецепты')
    def recipes_count(self, user):
        return user.recipes_count

    @admin.display(description='Подписки')
    def subscribed_to_count(self, user):
        return user.subscribed_to_count

    @admin.display(description='Подписчики')
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
        'tags_display'
    )
    list_filter = ('author__username', 'tags__name')
    search_fields = ['tags__name', 'name', 'author__username']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            favorited_count=Count('favorited_by', distinct=True),
        )

    @admin.display(description='Добавлено в избранное')
    def favorited_count(self, recipe):
        return recipe.favorited_count

    @admin.display(description='Автор')
    def author_link(self, recipe):
        url = reverse('admin:recipes_user_change', args=[recipe.author.id])
        return mark_safe(f'<a href="{url}">{recipe.author.username}</a>')

    @admin.display(description='Картинка')
    def image_tag(self, recipe):
        return mark_safe(
            f'<img src="{recipe.image.url}" width="100px" height="100px" />'
        )

    @admin.display(description='Теги')
    def tags_display(self, recipe):
        return mark_safe(
            '<br>'.join([tag.name for tag in recipe.tags.all()])
        )

    @admin.display(description='Продукты')
    def ingredients_display(self, recipe):
        ...


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ['measurement_unit']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscribing')


admin.site.unregister(Group)
admin.site.site_header = 'Foodgram Admin'
admin.site.site_title = 'Foodgram Admin Portal'
admin.site.index_title = (
    'Добро пожаловать на портал администратора Foodgram'
)
