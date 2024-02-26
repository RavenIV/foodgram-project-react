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
