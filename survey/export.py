from collections import defaultdict
import csv
import os.path
import tempfile
from typing import Dict, Set, Tuple, List, Iterable, TypeVar, Optional, Union
from uuid import UUID
import zipfile

import attr
from django.db import connection
import pandas as pd

from .models import Participant, ContextGroup, Context


def export_results(
        folder_name: str,
        only_complete: bool,
        participant_ids: Optional[Set[UUID]] = None,
        cs_group: Optional[str] = None,
        ) -> Tuple[bytes, str]:
    groups = {}  # participant_id -> context_set -> [{ctx}]
    named_contexts = get_named_contexts(cs_group=cs_group)
    with connection.cursor() as cursor:
        ctx_ids_by_cg = defaultdict(set)
        cursor.execute('select contextgroup_id, context_id '
                       'from survey_contextgroup_contexts')
        for cg_id, ctx_id in cursor.fetchall():
            ctx_ids_by_cg[cg_id].add(ctx_id)
    cg_qs = ContextGroup.objects.all()
    if cs_group:
        cg_qs = cg_qs.filter(context_set__group=cs_group)
    for cg in cg_qs:
        (groups
         .setdefault(cg.participant_id, {})
         .setdefault(cg.context_set_id, [])
         .append(ctx_ids_by_cg[cg.id])
         )
    n_to_group = {
        p.id: p.cs_to_group.count()
        for p in Participant.objects.prefetch_related('cs_to_group').all()}
    with tempfile.TemporaryDirectory() as dirname:
        archive_name = '{}.zip'.format(folder_name)
        archive_path = os.path.join(dirname, archive_name)
        with zipfile.ZipFile(archive_path, 'w') as archive:
            participants = set()
            write_csv = lambda sheet, name: _write_csv(
                sheet, archive, dirname, folder_name, name=name)
            for participant_id, p_groups in groups.items():
                if participant_ids is not None and \
                        participant_id not in participant_ids:
                    continue
                if only_complete and \
                        len(p_groups) != n_to_group[participant_id]:
                    continue  # not all grouped
                participants.add(participant_id)
                write_csv(p_groups_sheet(named_contexts, p_groups),
                          name='individual/{}'.format(participant_id))
            write_csv(participants_df(participants), name='personal')
            write_csv(words_df(named_contexts), name='words')
            true_groups = get_true_groups(named_contexts)
            write_csv(p_groups_sheet(named_contexts, true_groups),
                      name='model_classification')
        with open(archive_path, 'rb') as f:
            return f.read(), archive_name


@attr.s
class NamedContext:
    idx = attr.ib()
    name = attr.ib()
    is_filler = attr.ib()


def get_named_contexts(
        cs_group: Optional[str] = None) -> Dict[int, NamedContext]:
    named_contexts = {}
    cs_n = ctx_n = 0
    prev_cs = None
    qs = Context.objects.select_related('context_set')
    if cs_group is not None:
        qs = qs.filter(context_set__group=cs_group)
    for idx, ctx in enumerate(qs.order_by('context_set__id', 'order')):
        if prev_cs is None or ctx.context_set_id != prev_cs:
            cs_n += 1
            ctx_n = 1
        else:
            ctx_n += 1
        named_contexts[ctx.id] = NamedContext(
            idx=idx,
            name='set{}_stim{}'.format(cs_n, ctx_n),
            is_filler=ctx.context_set.is_filler,
        )
        prev_cs = ctx.context_set_id
    return named_contexts


class Sheet:
    def __init__(self):
        self.data = {}

    def write(self, row, col, value):
        self.data[row, col] = value

    def write_csv(self, f):
        writer = csv.writer(f)
        n_cols = max(col for _, col in self.data)
        n_rows = max(row for row, _ in self.data)
        for row in range(n_rows + 1):
            writer.writerow([
                self.data.get((row, col), '') for col in range(n_cols + 1)])


def p_groups_sheet(
        named_contexts: Dict[int, NamedContext],
        p_groups: Dict[int, List[Set[int]]]) -> Sheet:
    sheet = Sheet()
    # write header
    for named in sorted(
            named_contexts.values(), key=lambda x: x.idx):
        sheet.write(named.idx + 1, 0, named.name)
        sheet.write(0, named.idx + 1, named.name)

    def indices(x, y):
        return named_contexts[x].idx + 1, named_contexts[y].idx + 1

    # write cells
    for cs_groups in p_groups.values():
        all_ids = set()
        written = set()  # type: Set[Tuple[int, int]]
        for group in cs_groups:
            all_ids.update(group)
            for a, b in power(group):
                idx1, idx2 = indices(a, b)
                if idx1 >= idx2:
                    sheet.write(idx1, idx2, 1)
                    written.add((a, b))
            for a, b in power(all_ids):
                idx1, idx2 = indices(a, b)
                if idx1 > idx2 and (a, b) not in written:
                    sheet.write(idx1, idx2, 0)

    return sheet


def get_true_groups(
        named_contexts: Dict[int, NamedContext]) -> Dict[int, List[Set[int]]]:
    true_groups = {}
    for context in Context.objects.all():
        if context.id not in named_contexts:
            continue
        key = context.derivation.strip()
        (true_groups
         .setdefault(context.context_set_id, {})
         .setdefault(key, set()).add(context.id))
    return {cs_id: list(p_groups.values())
            for cs_id, p_groups in true_groups.items()}


T = TypeVar('T')


def power(lst: List[T]) -> Iterable[Tuple[T, T]]:
    return ((a, b) for a in lst for b in lst)


def participants_df(participants: Set[int]) -> pd.DataFrame:
    fields = ['person.id', 'profession', 'age', 'leading_hand', 'sex',
              'languages', 'education']
    data = []
    for p in Participant.objects.select_related('leading_hand', 'education'):
        if p.id in participants:
            row = {}
            for col, field in enumerate(fields):
                model_field = {'person.id': 'id'}.get(field, field)
                value = getattr(p, model_field)
                if not isinstance(value, int):
                    value = str(value or '')
                row[field] = value
            data.append(row)
    df = pd.DataFrame(data, columns=fields)
    df['type'] = 'naive'
    return df


def words_df(named_contexts: Dict[int, NamedContext]) -> pd.DataFrame:
    data = {
        (ctx.context_set.word,
         'POS_UNK',
         named_contexts[ctx.id].name.split('_')[0] + '_',
         )
        for ctx in Context.objects.select_related('context_set')
        if ctx.id in named_contexts}
    data = sorted(data, key=lambda x: int(x[2][3:-1]))
    return pd.DataFrame(data, columns=['word', 'POS', 'set'])


def _write_csv(
        data: Union[Sheet, pd.DataFrame],
        archive: zipfile.ZipFile,
        dirname, folder_name, name):
    filename = '{}.csv'.format(name)
    full_path = os.path.join(dirname, filename)
    parent = os.path.dirname(full_path)
    if not os.path.exists(parent):
        os.mkdir(parent)
    with open(full_path, 'wt') as f:
        if isinstance(data, Sheet):
            data.write_csv(f)
        else:
            data.to_csv(f, sep=';', index=None)
    archive.write(
        full_path, arcname='{}/{}'.format(folder_name, filename))
