import json

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from json into database'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)

    @staticmethod
    def check_filename(filename):
        if not filename.endswith('.json'):
            raise CommandError('Uknown file format. Only .json is supported.')
        return filename

    def handle(self, *args, **options):
        filename = self.check_filename(options['filename'])
        with open(filename, encoding='utf-8') as file:
            ingredients = Ingredient.objects.bulk_create(
                [Ingredient(**data) for data in json.load(file)]
            )
        self.stdout.write(self.style.SUCCESS(
            f'Successfully loaded {len(ingredients)} ingredients'
        ))
