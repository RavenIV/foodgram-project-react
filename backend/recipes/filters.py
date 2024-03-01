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
        bin_1 = (max_cook_time - min_cook_time) / 3
        result = recipes.aggregate(
            bin_0=min_cook_time,
            bin_1=bin_1,
            bin_2=bin_1 * 2,
            bin_3=max_cook_time + 1
        )
        if filter == 'fast':
            bin = (result['bin_0'], result['bin_1'])
        elif filter == 'medium':
            bin = (result['bin_1'], result['bin_2'])
        elif filter == 'long':
            bin = (result['bin_2'], result['bin_3'])
        return recipes.filter(cooking_time__gte=bin[0],
                              cooking_time__lt=bin[1])

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
