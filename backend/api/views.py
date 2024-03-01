from io import BytesIO

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewset
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import Ingredient, Recipe, Subscription, Tag, User
from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeSerializer,
    TagSerializer,
)
from .utils import create_shopping_list, get_subscribing_data

RECIPE_NOT_IN_FAVORITE = 'Рецепт {} не добавлен в избранное.'
RECIPE_IN_FAVORITE = 'Рецепт {} уже есть в избранном.'
RECIPE_NOT_IN_SHOPPING = 'Рецепт {} не добавлен в список покупок.'
RECIPE_IN_SHOPPING = 'Рецепт {} уже есть в списке покупок.'
SUBSCRIPTION_NOT_FOUND = 'Вы не подписаны на пользователя {}'
SUBSCRIBE_SELF = 'Нельзя подписаться на самого себя.'
EXIST_IN_SUBSCRIBING = 'Вы уже подписаны на пользователя {}'


class UserViewSet(DjoserUserViewset):
    http_method_names = ['get', 'post']

    def get_queryset(self):
        return User.objects.all()

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()


class SubscriptionsListView(ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.subscribed_to.all()

    def get_data(self, subscriptions):
        return [
            get_subscribing_data(
                subscription.subscribing, self.request
            ) for subscription in subscriptions
        ]

    def list(self, request, *args, **kwargs):
        subscriptions = self.get_queryset()
        page = self.paginate_queryset(subscriptions)
        if not page:
            return self.get_data(subscriptions)
        return self.get_paginated_response(self.get_data(page))


class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        subscribing = get_object_or_404(User, pk=user_id)
        user = request.user
        if subscribing == user:
            raise ValidationError(SUBSCRIBE_SELF)
        elif user.subscribed_to.filter(subscribing=subscribing).exists():
            raise ValidationError(
                EXIST_IN_SUBSCRIBING.format(subscribing.username)
            )
        Subscription.objects.create(user=user, subscribing=subscribing)
        return Response(get_subscribing_data(subscribing, request),
                        status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        subscribing = get_object_or_404(User, pk=user_id)
        get_object_or_404(
            Subscription, subscribing=subscribing, user=request.user
        ).delete()
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
            return [IsAuthenticated()]
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
        return FileResponse(
            BytesIO(create_shopping_list(request.user).encode('utf-8')),
            filename='shopping_list.txt',
            as_attachment=True
        )
