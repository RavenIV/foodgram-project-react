from django.urls import path, include
from rest_framework import routers

from .views import CustomUserViewSet, TagViewSet, IngredientViewSet

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='user')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingridient')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
