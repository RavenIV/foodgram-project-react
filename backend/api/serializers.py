from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT
from recipes.models import Ingredient, Recipe, RecipeProduct, Tag, User


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, user):
        current_user = self.context['request'].user
        return (
            current_user.is_authenticated
            and current_user.subscribed_to.filter(subscribing=user).exists()
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = fields


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields


class RecipeProductSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', read_only=False,
        required=True, queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )
    amount = serializers.IntegerField(min_value=MIN_INGREDIENT_AMOUNT)

    class Meta:
        model = RecipeProduct
        fields = (
            'id', 'name', 'measurement_unit', 'amount'
        )


class TagField(serializers.PrimaryKeyRelatedField):

    def to_representation(self, tag):
        return TagSerializer(tag).data


class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    author = UserSerializer(read_only=True)
    tags = TagField(many=True, queryset=Tag.objects.all())
    ingredients = RecipeProductSerializer(source='recipe_products', many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, recipe):
        user = self.context['request'].user
        return user.is_authenticated and user.favorite_recipes.filter(
            pk=recipe.id
        ).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user
        return user.is_authenticated and user.shopping_recipes.filter(
            pk=recipe.id
        ).exists()

    @staticmethod
    def check_empty(value):
        if not value:
            raise serializers.ValidationError('Пустое значение.')
        return value

    @staticmethod
    def check_duplicates(values):
        duplicates = {value.id for value in values if values.count(value) > 1}
        if duplicates:
            raise serializers.ValidationError(
                f'Значения дублируются: {duplicates}'
            )
        return values

    def validate_image(self, image):
        return self.check_empty(image)

    def validate_tags(self, tags):
        tags = self.check_empty(tags)
        return self.check_duplicates(tags)

    def validate_ingredients(self, products):
        self.check_duplicates([
            product['ingredient'] for product in self.check_empty(products)
        ])
        return products

    def create(self, validated_data):
        products = validated_data.pop('recipe_products')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        RecipeProduct.objects.bulk_create(
            RecipeProduct(recipe=recipe, **product)
            for product in products
        )
        return recipe

    def update(self, recipe, validated_data):
        if 'tags' in validated_data:
            recipe.tags.set(validated_data.pop('tags'))
        if 'recipe_products' in validated_data:
            recipe.ingredients.clear()
            RecipeProduct.objects.bulk_create(
                RecipeProduct(recipe=recipe, **product)
                for product in validated_data.pop('recipe_products')
            )
        return super().update(recipe, validated_data)


class RecipeReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscribingSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count')
        read_only_fields = fields

    def get_recipes(self, user):
        limit = int(
            self.context['request'].query_params.get('recipes_limit', 10**10)
        )
        return RecipeReadSerializer(user.recipes.all()[:limit], many=True).data

    def get_recipes_count(self, user):
        return user.recipes.count()
