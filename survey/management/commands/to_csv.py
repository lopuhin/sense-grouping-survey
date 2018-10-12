from collections import defaultdict

import pandas as pd
from django.db import connection
from django.core.management.base import BaseCommand

from survey.models import Context, ContextGroup


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('main_csv')
        parser.add_argument('contexts_csv')

    def handle(self, main_csv, contexts_csv, **options):
        with connection.cursor() as cursor:
            ctx_ids_by_cg = defaultdict(set)
            cursor.execute('select contextgroup_id, context_id '
                           'from survey_contextgroup_contexts')
            for cg_id, ctx_id in cursor.fetchall():
                ctx_ids_by_cg[cg_id].add(ctx_id)
        cgs_data = []
        for cg in (ContextGroup.objects
                .select_related('participant', 'context_set')):
            cgs_data.append({
                'contexts': ' '.join(map(str, ctx_ids_by_cg[cg.id])),
                'word': cg.context_set.word,
                'cs': cg.context_set.id,
                'is_filler': cg.context_set.is_filler,
                'group': cg.context_set.group,
                'participant': cg.participant.id,
                'source': cg.participant.source,
            })
        df = pd.DataFrame(
            cgs_data,
            columns=['participant', 'source', 'cs', 'is_filler', 'word',
                     'group', 'contexts']
        )
        df.to_csv(main_csv, index=None)
        contexts_df = pd.DataFrame(
            [{'id': c.id,
              'derivation': c.derivation,
              'text': c.text,
              'cs': c.context_set.id,
              }
             for c in Context.objects.all()],
            columns=['id', 'cs', 'derivation', 'text'])
        contexts_df.to_csv(contexts_csv, index=None)
