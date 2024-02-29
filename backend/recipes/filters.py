from django.contrib.admin import SimpleListFilter
from django.db.models import Sum


class SubscriptionListFilter(SimpleListFilter):
    title = 'Подписки'
    parameter_name = 'subscriptions'

    def lookups(self, request, model_admin):
        return (
            ('has_subscriptions', 'есть подписки'),
            ('has_subscribers', 'есть подписчики')
        )

    def queryset(self, request, users):
        if self.value() == 'has_subscriptions':
            return users.filter(subscribed_to__isnull=False)
        if self.value() == 'has_subscribers':
            return users.filter(subscribers__isnull=False)


class CookingTimeListFilter(SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def filter_recipes(self, recipes, filter):
        if not recipes:
            return
        bin = recipes.aggregate(Sum('cooking_time'))['cooking_time__sum'] / 3
        if filter == 'medium':
            bin *= 2
        if filter == 'long':
            bin *= 3
        return recipes.filter(cooking_time__lte=bin)

    def count_filter(self, recipes, filter):
        recipes = self.filter_recipes(recipes, filter)
        if not recipes:
            return 0
        return recipes.count()

    def lookups(self, request, model_admin):
        recipes = model_admin.get_queryset(request)
        lookups = []
        for filter, name in [
            ('fast', 'быстрые'),
            ('medium', 'средние'),
            ('long', 'долгие')
        ]:
            lookups.append(
                (filter, f'{name}: {self.count_filter(recipes, filter)}')
            )
        return lookups

    def queryset(self, request, recipes):
        if not self.value():
            return recipes
        return self.filter_recipes(recipes, self.value())
