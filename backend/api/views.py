from djoser.permissions import CurrentUserOrAdmin
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from recipes.models import Tag, Ingredient, Recipe
from .serializers import (
    TagSerializer, IngredientSerializer,
    RecipeSerializer
    # RecipeReadSerializer, RecipeCreateUpdateSerializer
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

    # def get_serializer_class(self):
    #     if self.action in ['list', 'retrieve']:
    #         return RecipeReadSerializer
    #     return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    # def perform_update(self, serializer):
    #     return serializer.save(author=self.request.user)

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     recipe = self.perform_create(serializer)
    #     recipe_serializer = RecipeReadSerializer(
    #         recipe, context={'request': request}
    #     )
    #     return Response(recipe_serializer.data, status=status.HTTP_201_CREATED)

    # def partial_update(self, request, *args, **kwargs):
    #     serializer = RecipeCreateUpdateSerializer(data=request.data, partial=True)
    #     serializer.is_valid(raise_exception=True)
    #     recipe = serializer.save()
    #     recipe_serializer = RecipeReadSerializer(
    #         recipe, context={'request': request}
    #     )
    #     return Response(recipe_serializer.data)
