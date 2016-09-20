import contextlib
import csv
import json
import os.path
import random
import tempfile
from typing import Dict, Set, Tuple, List, Iterable, TypeVar
import zipfile

import attr
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, reverse, HttpResponse
from django.utils import timezone
from django.views import View

from .forms import ParticipantForm, FeedbackForm
from .models import Participant, ContextGroup, Context, ContextSet


class Start(View):
    def get(self, request):
        return render(request, 'survey/start.html', {
            'form': ParticipantForm(),
            'source': request.GET.get('source', ''),
        })

    def post(self, request):
        form = ParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save()
            return json_response(
                {'next': reverse('survey_step', args=[participant])})
        else:
            return invalid_form_response(form)


class Group(View):
    def get(self, request, participant_id):
        participant = Participant.objects.get(pk=participant_id)
        grouped = set(
            ContextGroup.objects.filter(participant=participant)
            .values_list('context_set_id', flat=True))
        to_group = {}
        for context in Context.objects.select_related('context_set'):
            cs = context.context_set
            if cs.id not in grouped:
                cs_dict = to_group.setdefault(cs.id, {
                    'id': cs.id,
                    'word': capitalize_first(cs.word),
                    'contexts': []})
                cs_dict['contexts'].append(
                    {'id': context.id, 'text': context.text})
        to_group = list(to_group.values())
        random.shuffle(to_group)
        if not to_group:
            return redirect('survey_feedback', participant)
        total_to_group = ContextSet.objects.count()
        return render(request, 'survey/group.html', {
            'participant': participant,
            'to_group': json.dumps(to_group),
            'total_to_group': total_to_group,
            'done_contexts': total_to_group - len(to_group),
        })

    def post(self, request, participant_id):
        participant = Participant.objects.get(pk=participant_id)
        grouping = json.loads(request.POST['grouping'])
        context_set = None
        for group in grouping.values():
            group_contexts = []
            for ctx_id in group:
                context = Context.objects.get(pk=int(ctx_id))
                group_contexts.append(context)
                if context_set is None:
                    context_set = context.context_set
                    # clean up old contexts
                    (ContextGroup.objects
                        .filter(participant=participant, context_set=context_set)
                        .delete())
            if group_contexts:
                context_group = ContextGroup.objects.create(
                    participant=participant,
                    context_set=context_set)
                context_group.contexts.add(*group_contexts)
        return json_response({})


def capitalize_first(word):
    return word[0].upper() + word[1:]


class Feedback(View):
    def get(self, request, participant_id):
        participant = Participant.objects.get(pk=participant_id)
        form = FeedbackForm(instance=participant)
        return render(request, 'survey/feedback.html', {'form': form})

    def post(self, request, participant_id):
        participant = Participant.objects.get(pk=participant_id)
        form = FeedbackForm(request.POST, instance=participant)
        if form.is_valid():
            form.save()
            return json_response({})
        else:
            return invalid_form_response(form)


class Export(View):
    def get(self, request):
        groups = {}  # participant_id -> context_set -> [{ctx}]
        n_context_sets = ContextSet.objects.count()
        named_contexts = get_named_contexts()
        only_complete = 'all' not in request.GET
        for cs in ContextGroup.objects.prefetch_related('contexts'):
            (groups
             .setdefault(cs.participant_id, {})
             .setdefault(cs.context_set_id, [])
             .append({ctx.id for ctx in cs.contexts.all()})
             )
        with tempfile.TemporaryDirectory() as dirname:
            folder_name = 'SGS_Survey_{}'.format(
                timezone.now().strftime('%Y-%m-%d__%H_%M_%S'))
            archive_name = '{}.zip'.format(folder_name)
            archive_path = os.path.join(dirname, archive_name)
            with zipfile.ZipFile(archive_path, 'w') as archive:
                participants = set()
                write_csv = lambda sheet, name: _write_csv(
                    sheet, archive, dirname, folder_name, name=name)
                for participant_id, p_groups in groups.items():
                    if only_complete and len(p_groups) != n_context_sets:
                        continue  # not all grouped
                    participants.add(participant_id)
                    write_csv(
                        p_groups_sheet(named_contexts, p_groups),
                        name=participant_id)
                write_csv(
                    participants_sheet(participants), name='_participants')
                write_csv(
                    contexts_sheet(named_contexts), name='_contexts')
            with open(archive_path, 'rb') as f:
                response = HttpResponse(
                    f.read(), content_type='application/vnd.openxmlformats-'
                                           'officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = \
                    'attachment; filename="{}"'.format(archive_name)
                return response


@attr.s
class NamedContext:
    idx = attr.ib()
    name = attr.ib()


def get_named_contexts() -> Dict[int, NamedContext]:
    named_contexts = {}
    cs_n = ctx_n = 0
    prev_cs = None
    for idx, ctx in enumerate(
            Context.objects.order_by('context_set__id', 'order')):
        if prev_cs is None or ctx.context_set_id != prev_cs:
            cs_n += 1
            ctx_n = 1
        else:
            ctx_n += 1
        named_contexts[ctx.id] = NamedContext(
            idx=idx, name='set{}_stim{}'.format(cs_n, ctx_n))
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


def p_groups_sheet(named_contexts, p_groups) -> Sheet:
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


T = TypeVar('T')


def power(lst: List[T]) -> Iterable[Tuple[T, T]]:
    return ((a, b) for a in lst for b in lst)


def participants_sheet(participants: Set[int]) -> Sheet:
    sheet = Sheet()
    fields = ['id', 'started', 'finished', 'profession', 'age', 'leading_hand',
              'sex', 'languages', 'education', 'email', 'feedback']
    for col, field in enumerate(fields):
        sheet.write(0, col, field)
    row = 0
    for p in Participant.objects.select_related('leading_hand', 'education'):
        if p.id in participants:
            row += 1
            for col, field in enumerate(fields):
                value = getattr(p, field)
                if field == 'sex':
                    value = ['male', 'female'][int(value)]
                if not isinstance(value, int):
                    value = str(value or '')
                sheet.write(row, col, value)
    return sheet


def contexts_sheet(named_contexts):
    sheet = Sheet()
    sheet.write(0, 0, 'id')
    sheet.write(0, 1, 'word')
    sheet.write(0, 2, 'context')
    data = [(named_contexts[ctx.id].idx,
             [named_contexts[ctx.id].name, ctx.context_set.word, ctx.text])
            for ctx in Context.objects.select_related('context_set')]
    data.sort()
    for idx, row in data:
        for col, val in enumerate(row):
            sheet.write(idx + 1, col, val)
    return sheet


def _write_csv(
        sheet: Sheet, archive: zipfile.ZipFile, dirname, folder_name, name):
    filename = '{}.csv'.format(name)
    full_path = os.path.join(dirname, filename)
    with open(full_path, 'wt') as f:
        sheet.write_csv(f)
    archive.write(
        full_path, arcname='{}/{}'.format(folder_name, filename))


def json_response(data, response_cls=HttpResponse):
    return response_cls(json.dumps(data), content_type='text/json')


def invalid_form_response(form):
    # TODO - show it
    return json_response(
        {'error': str(form.errors())}, response_cls=HttpResponseBadRequest)
