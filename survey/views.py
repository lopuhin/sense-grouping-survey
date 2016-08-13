import contextlib
import json
import os.path
import random
import tempfile
from typing import Dict, Set
import zipfile

import attr
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, reverse, HttpResponse
from django.utils import timezone
from django.views import View
import xlsxwriter

from .forms import ParticipantForm, FeedbackForm
from .models import Participant, ContextGroup, Context, ContextSet


class Start(View):
    def get(self, request):
        return render(request, 'survey/start.html', {
            'form': ParticipantForm(),
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
                    'word': cs.word,
                    'contexts': []})
                cs_dict['contexts'].append(
                    {'id': context.id, 'text': context.text})
        to_group = list(to_group.values())
        random.shuffle(to_group)
        if not to_group:
            return redirect('survey_feedback', participant)
        return render(request, 'survey/group.html', {
            'participant': participant,
            'to_group': json.dumps(to_group),
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
    def get(self, _):
        groups = {}  # participant_id -> context_set -> [{ctx}]
        n_context_sets = ContextSet.objects.count()
        named_contexts = get_named_contexts()
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
                for participant_id, p_groups in groups.items():
                    if len(p_groups) != n_context_sets:
                        continue  # not all grouped
                    participants.add(participant_id)
                    with saving_book(archive, dirname, folder_name,
                                     name=participant_id) as book:
                        write_p_groups(book, named_contexts, p_groups)
                with saving_book(
                        archive, dirname, folder_name, '_participants') as book:
                    write_participants(book, participants)
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
    cs_n = ctx_n = 1
    prev_cs = None
    for idx, ctx in enumerate(
            Context.objects.order_by('context_set__id', 'order')):
        named_contexts[ctx.id] = NamedContext(
            idx=idx, name='set{}_stim{}'.format(cs_n, ctx_n))
        if prev_cs is not None and ctx.context_set_id != prev_cs:
            cs_n += 1
            ctx_n = 1
        else:
            ctx_n += 1
        prev_cs = ctx.context_set_id
    return named_contexts


def write_p_groups(book: xlsxwriter.Workbook, named_contexts, p_groups):
    sheet = book.add_worksheet()
    # write header
    for named in sorted(
            named_contexts.values(), key=lambda x: x.idx):
        sheet.write(named.idx, 0, named.name)
        sheet.write(0, named.idx, named.name)
    # write cells
    for cs_groups in p_groups.values():
        for group in cs_groups:
            for a, b in ((a, b) for a in group for b in group):
                idx1, idx2 = (named_contexts[a].idx,
                              named_contexts[b].idx)
                if idx1 > idx2:
                    sheet.write(idx1 + 1, idx2 + 1, 1)


def write_participants(book: xlsxwriter.Workbook, participants: Set[int]):
    sheet = book.add_worksheet()
    fields = ['id', 'profession', 'age', 'leading_hand',
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
                    value = str(value)
                sheet.write(row, col, value)


@contextlib.contextmanager
def saving_book(archive: zipfile.ZipFile, dirname, folder_name, name):
    filename = '{}.xlsx'.format(name)
    full_path = os.path.join(dirname, filename)
    with xlsxwriter.Workbook(full_path) as book:
        yield book
    archive.write(
        full_path, arcname='{}/{}'.format(folder_name, filename))


def json_response(data, response_cls=HttpResponse):
    return response_cls(json.dumps(data), content_type='text/json')


def invalid_form_response(form):
    # TODO - show it
    return json_response(
        {'error': str(form.errors())}, response_cls=HttpResponseBadRequest)
