from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from .models import (
    User, Recipe, Tag, Ingredient, Subscription,
    RecipeIngredients, Favorite, Shopping
)


class FavoriteInline(admin.TabularInline):
    model = Favorite
    extra = 0


class ShoppingInline(admin.TabularInline):
    model = Shopping
    extra = 0


class IngredientInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 0


class CustomUserAdmin(UserAdmin):
    list_filter = ('email', 'username')
    inlines = (FavoriteInline, ShoppingInline)


class RecipeAdmin(admin.ModelAdmin):
    inlines = [IngredientInline]
    list_display = ('name', 'author', 'favorited_count')
    list_filter = ('name', 'author', 'tags')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            favorited_count=Count('users_favorited', distinct=True),
        )

    def favorited_count(self, obj):
        return obj.favorited_count


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ['name']


admin.site.register(User, CustomUserAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(Subscription)
admin.site.register(Favorite)
admin.site.register(Shopping)
admin.site.site_header = 'Foodgram Admin'
admin.site.site_title = 'Foodgram Admin Portal'
admin.site.index_title = (
    'Добро пожаловать на портал администратора Foodgram'
)
