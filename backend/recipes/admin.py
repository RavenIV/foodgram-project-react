from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Recipe, Tag, Ingridient, Subscription,
    RecipeIngridients, Favorite, Shopping
)


class FavoriteInline(admin.TabularInline):
    model = Favorite
    extra = 0


class ShoppingInline(admin.TabularInline):
    model = Shopping
    extra = 0


class IngridientInline(admin.TabularInline):
    model = RecipeIngridients
    extra = 0


class CustomUserAdmin(UserAdmin):
    list_filter = ('email', 'username')
    inlines = (FavoriteInline, ShoppingInline)


class RecipeAdmin(admin.ModelAdmin):
    inlines = [IngridientInline]
    list_display = ('name', 'author', 'users_favorited')
    list_filter = ('name', 'author', 'tags')

    def users_favorited(self, obj):
        return obj.users_favorited.count()


class IngridientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ['name']


admin.site.register(User, CustomUserAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingridient, IngridientAdmin)
admin.site.register(Tag)
admin.site.register(Subscription)
