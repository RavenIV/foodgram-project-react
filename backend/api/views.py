from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.permissions import CurrentUserOrAdmin
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import CreateModelMixin, ListModelMixin, DestroyModelMixin
from rest_framework.viewsets import (
    ReadOnlyModelViewSet, ModelViewSet, GenericViewSet
)

from recipes.models import Tag, Ingredient, Recipe, User, Subscription
from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    TagSerializer, IngredientSerializer,
    RecipeSerializer, SubscriptionSerializer
)


class CustomUserViewSet(UserViewSet):
    http_method_names = ['get', 'post']

    @action(["get"], detail=False, permission_classes=[CurrentUserOrAdmin])
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        if request.method == "GET":
            return self.retrieve(request, *args, **kwargs)


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
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)


class ListCreateDestroyViewSet(CreateModelMixin,
                               ListModelMixin,
                               DestroyModelMixin,
                               GenericViewSet):
    pass


class SubscriptionViewSet(ListCreateDestroyViewSet):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return self.request.user.subscribing.all()
    
    # def get_subscribing_user(self):
    #     return get_object_or_404(User, pk=self.kwargs.get('user_id'))

    # def perform_create(self, serializer):
    #     serializer.save(
    #         user=self.request.user,
    #         subscribing=self.get_subscribing_user()
    #     )

    # def get_object(self):
    #     return get_object_or_404(
    #         Subscription,
    #         user=self.request.user,
    #         subscribing=self.get_subscribing_user()
    #     )
