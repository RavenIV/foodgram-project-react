from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes import constants
from recipes.models import Ingredient, Recipe, RecipeProduct, Subscription, Tag, User


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


class MealSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', read_only=False,
        required=True, queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )
    amount = serializers.IntegerField(
        min_value=constants.MIN_INGREDIENT_AMOUNT
    )

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
    ingredients = MealSerializer(source='recipe_products', many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=constants.MIN_COOKING_TIME
    )

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

    def validate(self, data):
        tags = data.get('tags')
        meal = data.get('recipe_products')
        if not tags:
            raise serializers.ValidationError({'tags': constants.ADD_TAGS})
        if not meal:
            raise serializers.ValidationError({
                'ingredients': constants.ADD_INGREDIENTS
            })
        ingredients = [ingredient['ingredient'] for ingredient in meal]
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError({
                'tags': constants.DUPLICATE_TAGS
            })
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError({
                'ingredients': constants.DUPLICATE_INGREDIENTS
            })
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('recipe_products')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        RecipeProduct.objects.bulk_create([
            RecipeProduct(recipe=recipe, **ingredient) for ingredient in ingredients
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


class RecipeFavoriteShoppingSerializer(serializers.ModelSerializer):
    favorited_by = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=User.objects.all(), required=False
    )
    shopped_by = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=User.objects.all(), required=False
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'cooking_time', 'favorited_by', 'shopped_by'
        )
        read_only_fields = fields

    def update(self, recipe, validated_data):
        user_favorited = validated_data.get('favorited_by')
        user_shopped = validated_data.get('shopped_by')
        if user_favorited:
            if user_favorited in recipe.favorited_by.all():
                raise serializers.ValidationError(constants.RECIPE_IN_FAVORITE)
            recipe.favorited_by.add(user_favorited)
        elif user_shopped:
            if user_shopped in recipe.shopped_by.all():
                raise serializers.ValidationError(constants.RECIPE_IN_SHOPPING)
            recipe.shopped_by.add(user_shopped)
        return recipe


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
            raise serializers.ValidationError(constants.SUBSCRIBE_SELF)
        elif user.subscribed_to.filter(subscribing=subscribing).exists():
            raise serializers.ValidationError(constants.EXIST_IN_SUBSCRIBING)
        return data

    def to_representation(self, subscription):
        subscribing = subscription.subscribing
        user_serializer = UserSerializer(subscribing, context=self.context)
        limit = int(self.context['request'].query_params.get(
            'recipes_limit', 10**10
        ))
        recipe_serializer = RecipeFavoriteShoppingSerializer(
            subscribing.recipes.all()[:limit], many=True
        )
        return dict(
            **user_serializer.data,
            recipes=recipe_serializer.data,
            recipes_count=subscribing.recipes.count()
        )
