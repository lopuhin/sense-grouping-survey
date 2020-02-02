from pathlib import Path
from uuid import UUID

from django.core.management.base import BaseCommand

from survey.export import export_results


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

    def handle(self, output_zip, participant_ids=None, **options):
        assert output_zip.endswith('.zip')
        folder_name, _ = output_zip.rsplit('.zip', 1)
        if participant_ids:
            participant_ids = {
                UUID(line.strip()) for line in
                Path(participant_ids).read_text('utf8').splitlines()}
        data, _ = export_results(
            folder_name,
            # FIXME this is wrong but it does not work in any case
            only_complete=options['all'],
            participant_ids=participant_ids,
        )
        Path(output_zip).write_bytes(data)
