import base64

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from recipes.models import Tag, Ingredient, Recipe, Meal

User = get_user_model()


class FoodgramUserCreateSerializer(UserCreateSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )


class FoodgramUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, user):
        return user in user.subscribing.all()


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class MealSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', read_only=False,
        required=True, queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = Meal
        fields = (
            'id', 'name', 'measurement_unit', 'amount'
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    author = FoodgramUserSerializer(read_only=True)
    ingredients = MealSerializer(
        source='meal_set', many=True, read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = fields

    def get_user(self):
        return self.context['request'].user

    def get_is_favorited(self, recipe):
        if isinstance(self.get_user(), AnonymousUser):
            return False
        return recipe in self.get_user().favorite_recipes.all()

    def get_is_in_shopping_cart(self, recipe):
        if isinstance(self.get_user(), AnonymousUser):
            return False
        return recipe in self.get_user().shopping_cart.all()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, image = data.split(';base64,')
            extension = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(image), name=f'temp.{extension}'
            )
        return super().to_internal_value(data)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = MealSerializer(
        many=True, source='meal_set', required=True,
    )
    image = Base64ImageField(required=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=True,
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags',
            'image', 'name', 'text', 'cooking_time'
        )

    def validate(self, data):
        tags = data.get('tags')
        meal = data.get('meal_set')
        ingredients = [ingredient['ingredient'] for ingredient in meal]
        if (
            not tags or meal or len(tags) != len(set(tags))
            or len(ingredients) != len(set(ingredients))
        ):
            raise serializers.ValidationError()
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
