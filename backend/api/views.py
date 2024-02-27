from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewset
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import Ingredient, Recipe, Subscription, Tag, User
from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly, IsAuthenticatedAndReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeSerializer,
    SubscriptionSerializer,
    TagSerializer
)
from .utils import create_shopping_list

RECIPE_NOT_IN_FAVORITE = 'Рецепт {} не добавлен в избранное.'
RECIPE_IN_FAVORITE = 'Рецепт {} уже есть в избранном.'
RECIPE_NOT_IN_SHOPPING = 'Рецепт {} не добавлен в список покупок.'
RECIPE_IN_SHOPPING = 'Рецепт {} уже есть в списке покупок.'
SUBSCRIPTION_NOT_FOUND = 'Вы не подписаны на пользователя {}'


class UserViewSet(DjoserUserViewset):
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        if self.action == 'subscriptions':
            return self.request.user.subscribed_to.all()
        return User.objects.all()

    def get_permissions(self):
        if self.action in ['subscriptions', 'subscribe']:
            self.permission_classes = [IsAuthenticated]
        if self.action == 'me':
            self.permission_classes = [IsAuthenticatedAndReadOnly]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ['subscriptions', 'subscribe']:
            return SubscriptionSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer, *args, **kwargs):
        return super(DjoserUserViewset, self).perform_create(serializer)

    @action(['get'], detail=False)
    def subscriptions(self, request):
        return self.list(request)

    @action(['post', 'delete'], detail=True)
    def subscribe(self, request, id=None):
        subscribing = self.get_object()
        if request.method == 'POST':
            request.data['subscribing'] = subscribing.pk
            return self.create(request)
        if request.method == 'DELETE':
            try:
                Subscription.objects.get(
                    subscribing=subscribing, user=request.user
                ).delete()
            except Subscription.DoesNotExist:
                raise ValidationError({
                    'errors': SUBSCRIPTION_NOT_FOUND.format(subscribing)
                })
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [SearchFilter]
    search_fields = ['^name']


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.prefetch_related(
        'ingredients', 'tags', 'author'
    )
    http_method_names = ['get', 'post', 'patch', 'delete']
    serializer_class = RecipeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [IsAuthorOrReadOnly]

    def get_permissions(self):
        if self.action in [
            'favorite', 'shopping_cart', 'download_shopping_cart'
        ]:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    @staticmethod
    def add_favorited_or_shopped_by(request, recipe, recipe_set, message):
        if request.user in recipe_set.all():
            raise ValidationError({'errors': message})
        recipe_set.add(request.user)
        return Response(RecipeReadSerializer(recipe).data,
                        status=status.HTTP_201_CREATED)

    @staticmethod
    def remove_favorited_or_shopped_by(request, object_set, message):
        if request.user not in object_set.all():
            raise ValidationError({'errors': message})
        object_set.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['post', 'delete'], detail=True)
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            return self.add_favorited_or_shopped_by(
                request, recipe, recipe.favorited_by,
                RECIPE_IN_FAVORITE.format(recipe.name)
            )
        elif request.method == 'DELETE':
            return self.remove_favorited_or_shopped_by(
                request, recipe.favorited_by,
                RECIPE_NOT_IN_FAVORITE.format(recipe.name)
            )

    @action(['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            return self.add_favorited_or_shopped_by(
                request, recipe, recipe.shopped_by,
                RECIPE_IN_SHOPPING.format(recipe.name)
            )
        elif request.method == 'DELETE':
            return self.remove_favorited_or_shopped_by(
                request, recipe.shopped_by,
                RECIPE_NOT_IN_SHOPPING.format(recipe.name)
            )

    @action(['get'], detail=False)
    def download_shopping_cart(self, request):
        return FileResponse(create_shopping_list(request.user),
                            filename='shopping_list.txt',
                            as_attachment=True)
