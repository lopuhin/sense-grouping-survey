import csv

from django.core.management.base import BaseCommand

from survey.models import Context, ContextSet


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('csv_path')

    def handle(self, csv_path, **options):
        with open(csv_path) as f:
            reader = csv.reader(f)
            _ = next(reader)  # skip header
            context_set = None
            prev_word = None
            for word, order, text in reader:
                if prev_word != word:
                    context_set = ContextSet.objects.create(word=word)
                Context.objects.create(
                    context_set=context_set,
                    order=float(order),
                    text=text)
                prev_word = word
