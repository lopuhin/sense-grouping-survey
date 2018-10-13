from pathlib import Path

from django.core.management.base import BaseCommand

from survey.views import export_results


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('output_zip')
        parser.add_argument(
            '--all', action='store_true',
            help='export even results for participants who '
                 'didn\'t finish all tasks')
        parser.add_argument(
            '--participant-ids',
            help='a text file with participant ids')

    def handle(self, output_zip, **options):
        # TODO filter participants
        data, _ = export_results(only_complete=options['all'])
        Path(output_zip).write_bytes(data)

