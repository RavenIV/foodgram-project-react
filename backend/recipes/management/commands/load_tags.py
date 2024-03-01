import json

from recipes.models import Tag
from .load_ingredients import Command as BaseCommand


class Command(BaseCommand):
    help = 'Load tags from json into database'

    def handle(self, *args, **options):
        filename = self.check_filename(options['filename'])
        with open(filename, encoding='utf-8') as file:
            tags = Tag.objects.bulk_create(
                [Tag(**data) for data in json.load(file)]
            )
        self.stdout.write(self.style.SUCCESS(
            f'Successfully loaded {len(tags)} tags.'
        ))
