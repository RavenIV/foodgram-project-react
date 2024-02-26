from django.contrib.admin import SimpleListFilter


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

    def lookups(self, request, model_admin):
        return (
            ('fast', 'быстрые (до 30 мин)'),
            ('medium', 'средние (до 60 мин)'),
            ('long', 'долгие (от 60 мин)')
        )

    def queryset(self, request, recipes):
        if self.value() == 'fast':
            return recipes.filter(cooking_time__lt=30)
        if self.value() == 'medium':
            return recipes.filter(cooking_time__gte=30, cooking_time__lt=60)
        if self.value() == 'long':
            return recipes.filter(cooking_time__gte=60)
