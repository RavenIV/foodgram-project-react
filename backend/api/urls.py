from django.urls import path, include
from rest_framework import routers

from .views import (
    CustomUserViewSet, TagViewSet, IngredientViewSet,
    RecipeViewSet, 
    # SubscriptionViewSet

)
app_name = 'api'

router = routers.DefaultRouter()
# router.register(r'users/(?P<user_id>\d+)/subscribe', SubscriptionViewSet, basename='subscribe')
# # router.register(r'users/subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'users', CustomUserViewSet, basename='user')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingridient')
router.register(r'recipes', RecipeViewSet, basename='recipe')


# class CustomRouter(routers.SimpleRouter):
#     routes = [
#         routers.DynamicRoute(
#             url=r'^{prefix}/{lookup}/{url_path}&',
#             # mapping={'post': 'create', 'delete': 'destroy'},
#             name='{basename}-{url_name}',
#             detail=True,
#             initkwargs={}
#         )
#     ]


# custom_router = CustomRouter()
# custom_router.register(r'users/(?P<user_id>\d+)/subscribe', SubscriptionViewSet, basename='subscribe')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
    # path('', include(custom_router.urls))
]
