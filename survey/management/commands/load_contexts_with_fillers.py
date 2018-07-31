import csv

from django.core.management.base import BaseCommand

from survey.models import Context, ContextSet


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('csv_path')

    def handle(self, csv_path, **options):
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            context_set = None
            prev_word = None
            order = 0  # no explicit order in the file
            for item in reader:
                word = item['word'].strip()
                assert item['type'] in {'fill', 'stim'}
                if prev_word != word:
                    context_set = ContextSet.objects.create(
                        word=word,
                        is_filler=item['type'] == 'fill',
                        group=item['group'],
                    )
                    order = 0
                Context.objects.create(
                    context_set=context_set,
                    order=float(order),
                    text=item['context'],
                    derivation=item['derivation'],
                )
                prev_word = word
                order += 1
