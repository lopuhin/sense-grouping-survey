import json
import random

from django.views import View
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, Http404, reverse, HttpResponse

from .forms import ParticipantForm, FeedbackForm
from .models import Participant, ContextGroup, Context


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
            return redirect('survery_feedback', participant)
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


def json_response(data, response_cls=HttpResponse):
    return response_cls(json.dumps(data), content_type='text/json')


def invalid_form_response(form):
    # TODO - show it
    return json_response(
        {'error': str(form.errors())}, response_cls=HttpResponseBadRequest)
