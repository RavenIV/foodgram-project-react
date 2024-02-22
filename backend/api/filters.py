from django_filters import rest_framework as filters

from recipes.models import Recipe, Tag, User


class RecipeFilter(filters.FilterSet):
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_shopping')

    class Meta:
        model = Recipe
        fields = (
            'author', 'is_favorited', 'tags', 'is_in_shopping_cart',
        )

    def filter_favorited(self, queryset, name, value):
        if self.request is None:
            return Recipe.objects.none()
        if not self.request.user.is_authenticated:
            return queryset
        if not value:
            return queryset.exclude(favorited_by=self.request.user)
        return queryset.filter(favorited_by=self.request.user)

    def filter_shopping(self, queryset, name, value):
        if self.request is None:
            return Recipe.objects.none()
        if not self.request.user.is_authenticated:
            return queryset
        if not value:
            return queryset.exclude(shopped_by=self.request.user)
        return queryset.filter(shopped_by=self.request.user)
