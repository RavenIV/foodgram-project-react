from django.urls import include, path
from rest_framework import routers

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet, SubscriptionsListView, SubscribeView

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('users/subscriptions/', SubscriptionsListView.as_view(), name='subscriptions'),
    path('users/<int:user_id>/subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('', include(router.urls)),
]
