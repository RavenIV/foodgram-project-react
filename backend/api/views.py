from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.permissions import CurrentUserOrAdmin
from djoser.views import UserViewSet as DjoserUserViewset
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import (
    ReadOnlyModelViewSet, ModelViewSet,
)

from recipes.constants import (
    RECIPE_NOT_FOUND, RECIPE_NOT_IN_FAVORITE,
    RECIPE_NOT_IN_SHOPPING, SUBSCRIPTION_NOT_FOUND
)
from recipes.models import Tag, Ingredient, Recipe, User, Subscription
from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    TagSerializer, IngredientSerializer,
    RecipeSerializer,
    SubscriptionSerializer,
    RecipeShortReadSerializer
)


class UserViewSet(DjoserUserViewset):
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        if self.action == 'subscriptions':
            return self.request.user.subscribing.all()
        return User.objects.all()

    def get_serializer_class(self):
        if self.action == 'subscriptions':
            return SubscriptionSerializer
        return super().get_serializer_class()

    @action(['get'], detail=False, permission_classes=[CurrentUserOrAdmin])
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(['get'], detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        return self.list(request)

    @action(['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        subscribing = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(subscribing=subscribing)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            try:
                subscription = Subscription.objects.get(
                    subscribing=subscribing, user=request.user
                )
                subscription.delete()
            except Subscription.DoesNotExist:
                raise ValidationError(
                    {'errors': SUBSCRIPTION_NOT_FOUND.format(subscribing)}
                )
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
    search_fields = ['name']


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.prefetch_related(
        'ingredients', 'tags', 'author'
    )
    http_method_names = ['get', 'post', 'patch', 'delete']
    serializer_class = RecipeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_permissions(self):
        actions = ['favorite', 'shopping_cart', 'download_shopping_cart']
        self.permission_classes = [
            IsAuthenticated if self.action in actions else IsAuthorOrReadOnly
        ]
        return super().get_permissions()

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def add_favorited_or_shopped_by(self, pk, request):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            raise ValidationError({'errors': RECIPE_NOT_FOUND.format(pk)})
        serializer = RecipeShortReadSerializer(recipe, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_favorited_or_shopped_by(self, request, object_set, message):
        if request.user not in object_set.all():
            raise ValidationError({'errors': message})
        object_set.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['post', 'delete'], detail=True)
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            request.data['favorited_by'] = request.user.id
            return self.add_favorited_or_shopped_by(pk, request)
        elif request.method == 'DELETE':
            return self.remove_favorited_or_shopped_by(
                request, self.get_object().favorited_by,
                RECIPE_NOT_IN_FAVORITE.format(pk)
            )

    @action(['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            request.data['shopped_by'] = request.user.id
            return self.add_favorited_or_shopped_by(pk, request)
        elif request.method == 'DELETE':
            return self.remove_favorited_or_shopped_by(
                request, self.get_object().shopped_by,
                RECIPE_NOT_IN_SHOPPING.format(pk)
            )

    @action(['get'], detail=False)
    def download_shopping_cart(self, request):
        data = [(
            f'{ingredient.name} ({ingredient.measurement_unit}) - '
            f'{ingredient.total_amount} \n'
        ) for ingredient in Ingredient.objects.filter(
            recipes__shopped_by=request.user
        ).annotate(total_amount=Sum('meal__amount'))
        ]
        return HttpResponse(data, headers={
            'Content-Type': 'text/plain',
            'Content-Disposition': 'attachment; filename="shopping_list.txt"'
        })
