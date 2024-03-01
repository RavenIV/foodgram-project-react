from django.contrib.admin import SimpleListFilter
from django.db.models import Max, Min


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

    @staticmethod
    def filter_recipes(recipes, filter):
        if not recipes or not filter:
            return recipes
        max_cook_time = Max('cooking_time', default=0)
        min_cook_time = Min('cooking_time', default=0)
        bin = (max_cook_time - min_cook_time) / 3
        result = recipes.aggregate(
            min_cook_time=min_cook_time,
            medium_cook_time=bin,
            long_cook_time=bin * 2,
            max_cook_time=max_cook_time + 1
        )
        if filter == 'fast':
            interval = (result['min_cook_time'], result['medium_cook_time'])
        elif filter == 'medium':
            interval = (result['medium_cook_time'], result['long_cook_time'])
        elif filter == 'long':
            interval = (result['long_cook_time'], result['max_cook_time'])
        return recipes.filter(cooking_time__gte=interval[0],
                              cooking_time__lt=interval[1])

    def lookups(self, request, model_admin):
        recipes = model_admin.get_queryset(request)
        return (
            (lookup, name.format(self.filter_recipes(recipes, lookup).count()))
            for lookup, name in [
                ('fast', 'быстрые: {}'),
                ('medium', 'средние: {}'),
                ('long', 'долгие: {}')
            ]
        )

    def queryset(self, request, recipes):
        return self.filter_recipes(recipes, self.value())
