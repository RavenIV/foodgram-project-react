# Generated by Django 3.2.16 on 2024-02-13 13:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='favorite',
            options={'verbose_name': 'Избранное', 'verbose_name_plural': 'избранные'},
        ),
        migrations.AlterModelOptions(
            name='ingridient',
            options={'verbose_name': 'Ингредиент', 'verbose_name_plural': 'ингредиенты'},
        ),
        migrations.AlterModelOptions(
            name='recipeingridients',
            options={'verbose_name': 'Ингредиенты рецепта', 'verbose_name_plural': 'ингредиенты рецептов'},
        ),
        migrations.AlterModelOptions(
            name='shoppingcart',
            options={'verbose_name': 'Корзина покупок', 'verbose_name_plural': 'корзины покупок'},
        ),
        migrations.AlterField(
            model_name='recipeingridients',
            name='ingridient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='recipes.ingridient', verbose_name='Ингредиент'),
        ),
        migrations.AlterField(
            model_name='recipeingridients',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.recipe', verbose_name='Рецепт'),
        ),
    ]