import base64

from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from djoser.serializers import UserCreateSerializer as DjoserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from recipes.constants import (
    ADD_TAGS, ADD_INGREDIENTS, DUPLICATE_TAGS, DUPLICATE_INGREDIENTS,
    RECIPE_IN_FAVORITE, RECIPE_IN_SHOPPING, SUBSCRIBE_SELF,
    EXIST_IN_SUBSCRIBING, MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT
)
from recipes.models import Tag, Ingredient, Recipe, Meal, Subscription, User


class UserCreateSerializer(DjoserSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )


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
            and current_user.subscribing.filter(subscribing=user).exists()
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
        validators=[MinValueValidator(MIN_INGREDIENT_AMOUNT)]
    )

    class Meta:
        model = Meal
        fields = (
            'id', 'name', 'measurement_unit', 'amount'
        )


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, image = data.split(';base64,')
            extension = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(image), name=f'temp.{extension}'
            )
        return super().to_internal_value(data)


class TagField(serializers.PrimaryKeyRelatedField):

    def to_representation(self, value):
        return TagSerializer(value).data


class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    author = UserSerializer(read_only=True)
    tags = TagField(many=True, queryset=Tag.objects.all())
    ingredients = MealSerializer(source='meal_set', many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=[MinValueValidator(MIN_COOKING_TIME)]
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
        meal = data.get('meal_set')
        if not tags:
            raise serializers.ValidationError({'tags': ADD_TAGS})
        if not meal:
            raise serializers.ValidationError({'ingredients': ADD_INGREDIENTS})
        ingredients = [ingredient['ingredient'] for ingredient in meal]
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError({'tags': DUPLICATE_TAGS})
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError({
                'ingredients': DUPLICATE_INGREDIENTS
            })
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('meal_set')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags_data:
            recipe.tags.add(tag)
        for ingredient in ingredients_data:
            Meal.objects.create(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
        return recipe

    def update(self, recipe, validated_data):
        recipe.name = validated_data.get('name', recipe.name)
        recipe.image = validated_data.get('image', recipe.image)
        recipe.text = validated_data.get('text', recipe.text)
        recipe.cooking_time = validated_data.get(
            'cooking_time', recipe.cooking_time
        )
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            recipe.tags.set([tag for tag in tags_data])
        if 'meal_set' in validated_data:
            ingredients_data = validated_data.pop('meal_set')
            recipe.ingredients.clear()
            for data in ingredients_data:
                recipe.ingredients.add(
                    data['ingredient'],
                    through_defaults={'amount': data['amount']}
                )
        recipe.save()
        return recipe


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
                raise serializers.ValidationError(RECIPE_IN_FAVORITE)
            recipe.favorited_by.add(user_favorited)
        elif user_shopped:
            if user_shopped in recipe.shopped_by.all():
                raise serializers.ValidationError(RECIPE_IN_SHOPPING)
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
            raise serializers.ValidationError(SUBSCRIBE_SELF)
        elif user.subscribing.filter(subscribing=subscribing).exists():
            raise serializers.ValidationError(EXIST_IN_SUBSCRIBING)
        return data

    def to_representation(self, subscription):
        subscribing = subscription.subscribing
        user_serializer = UserSerializer(
            subscribing, context=self.context
        )
        recipes = subscribing.recipes.all()
        recipes_count = recipes.count()
        limit = self.context['request'].query_params.get('recipes_limit')
        recipe_serializer = RecipeFavoriteShoppingSerializer(
            recipes[:int(limit) if limit else recipes_count],
            many=True
        )
        return dict(
            user_serializer.data,
            recipes=recipe_serializer.data,
            recipes_count=recipes_count
        )
