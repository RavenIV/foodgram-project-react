from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT
from recipes.models import (
    Ingredient, Recipe, RecipeProduct,
    Subscription, Tag, User
)

SUBSCRIBE_SELF = 'Нельзя подписаться на самого себя.'
EXIST_IN_SUBSCRIBING = 'Вы уже подписаны на пользователя {}'


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
    def validate(data):
        for field in ['tags', 'recipe_products', 'image']:
            values = data.get(field)
            if not values:
                raise serializers.ValidationError({field: 'Пустое значение.'})
            if field == 'recipe_products':
                values = [value['ingredient'] for value in values]
            if isinstance(values, list):
                duplicates = {
                    value for value in values if values.count(value) > 1
                }
                if duplicates:
                    raise serializers.ValidationError(
                        {field: f'Значения дублируются: {duplicates}'}
                    )
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('recipe_products')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        RecipeProduct.objects.bulk_create([
            RecipeProduct(recipe=recipe, **ingredient)
            for ingredient in ingredients
        ])
        return recipe

    def update(self, recipe, validated_data):
        if 'tags' in validated_data:
            recipe.tags.set(validated_data.pop('tags'))
        if 'recipe_products' in validated_data:
            recipe.ingredients.clear()
            RecipeProduct.objects.bulk_create([
                RecipeProduct(recipe=recipe, **ingredient)
                for ingredient in validated_data.pop('recipe_products')
            ])
        return super().update(recipe, validated_data)


class RecipeReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    subscribing = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=User.objects.all()
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Subscription
        fields = ('user', 'subscribing')

    def validate(self, data):
        subscribing = data['subscribing']
        user = self.context['request'].user
        if subscribing == user:
            raise serializers.ValidationError(SUBSCRIBE_SELF)
        elif user.subscribed_to.filter(subscribing=subscribing).exists():
            raise serializers.ValidationError(
                EXIST_IN_SUBSCRIBING.format(subscribing.username)
            )
        return data

    def to_representation(self, subscription):
        subscribing = subscription.subscribing
        user_serializer = UserSerializer(subscribing, context=self.context)
        limit = int(self.context['request'].query_params.get(
            'recipes_limit', 10**10
        ))
        recipe_serializer = RecipeReadSerializer(
            subscribing.recipes.all()[:limit], many=True
        )
        return dict(
            **user_serializer.data,
            recipes=recipe_serializer.data,
            recipes_count=subscribing.recipes.count()
        )
