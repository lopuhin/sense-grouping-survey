from collections import Counter, defaultdict
import json
import random

from django.db.models import Count
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, reverse, HttpResponse
from django.utils import timezone
from django.views import View

from .forms import ParticipantForm, FeedbackForm
from .models import Participant, ContextGroup, Context, ContextSet
from .export import export_results


# Number of filler and stimuli for each participant
# Note that stats view and template have hardcoded thresholds
# which also need to be updated in case the total number of contexts changes.
N_FILLERS = 3
N_STIMULI = 7


class Start(View):
    def get(self, request):
        return render(request, 'survey/start.html', {
            'form': ParticipantForm(),
            'source': request.GET.get('source', ''),
        })

    def post(self, request):
        form = ParticipantForm(request.POST)
        if form.is_valid():
            cs_fillers, cs_stimuli = [], []
            for cs in ContextSet.objects.all():
                (cs_fillers if cs.is_filler else cs_stimuli).append(cs)
            cs_to_group = (random.sample(cs_fillers, N_FILLERS) +
                           random.sample(cs_stimuli, N_STIMULI))
            participant = form.save()
            participant.cs_to_group.add(*cs_to_group)
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
        participant_cs_to_group = {
            cs.id for cs in participant.cs_to_group.all()}
        for context in Context.objects.select_related('context_set'):
            cs = context.context_set
            if cs.id not in grouped and cs.id in participant_cs_to_group:
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
        for cs_dict in to_group:
            random.shuffle(cs_dict['contexts'])
        total_to_group = len(participant_cs_to_group)
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
                        .filter(participant=participant,
                                context_set=context_set)
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


class Stats(View):
    def get(self, request):
        started_by_source = Counter(
            p.source for p in Participant.objects.all())
        stats_by_source = {source: defaultdict(int, started=started)
                           for source, started in started_by_source.items()}
        n_context_sets = N_STIMULI + N_FILLERS
        for x in (ContextGroup.objects
                  .values('participant', 'participant__source')
                  .annotate(Count('context_set', distinct=True))):
            count = x['context_set__count']
            source = x['participant__source']
            if count == n_context_sets:
                stats_by_source[source]['finished'] += 1
            threshold = 0
            while threshold < n_context_sets:
                threshold += 2
                if count >= threshold:
                    stats_by_source[source]['done_{}'.format(threshold)] += 1
        return render(request, 'survey/stats.html', {
            'stats_by_source': sorted(
                (source, stats) for source, stats in stats_by_source.items()
            )})


class Export(View):
    def get(self, request):
        folder_name = 'SGS_Survey_{}'.format(
            timezone.now().strftime('%Y-%m-%d__%H_%M_%S'))
        data, name = export_results(
            folder_name, only_complete='all' not in request.GET)
        response = HttpResponse(data, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{name}"'
        return response


def json_response(data, response_cls=HttpResponse):
    return response_cls(json.dumps(data), content_type='text/json')


def invalid_form_response(form):
    # TODO - show it
    return json_response(
        {'error': str(form.errors())}, response_cls=HttpResponseBadRequest)
