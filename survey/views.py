import json

from django.views import View
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, Http404, reverse, HttpResponse

from .forms import ParticipantForm, FeedbackForm
from .models import Participant, ContextSet, ContextGroup


class Start(View):
    def get(self, request):
        return render(request, 'survey/start.html', {
            'form': ParticipantForm(),
        })

    def post(self, request):
        result = {}
        form = ParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save()
            result['next'] = reverse('survey_step', args=[str(participant.id), 0])
            response_cls = HttpResponse
        else:
            response_cls = HttpResponseBadRequest
            result['error'] = str(form.errors())
        return response_cls(json.dumps(result), content_type='text/json')


class Step(View):
    def get(self, request, participant_id, step):
        step = int(step)
        participant = Participant.objects.get(pk=participant_id)
        try:
            context_set = ContextSet.objects.all()[step]
        except IndexError:
            raise Http404
        disabled = (
            ContextGroup.objects
                .filter(participant=participant, context_set=context_set)
                .exists())
        last_step = ContextSet.objects.count() - 1
        contexts = list(context_set.context_set.all())
        return render(request, 'survey/step.html', {
            'participant': participant,
            'word': context_set.word,
            'contexts': contexts,
            'disabled': disabled,
            'next_step': (step + 1) if step < last_step else None,
        })


def survey_feedback(request, participant_id):
    participant = Participant.objects.get(pk=participant_id)
    if request.method == 'POST':
        form = FeedbackForm(request.POST, instance=participant)
        if form.is_valid():
            form.save()
            return redirect('finish_survey')
    else:
        form = FeedbackForm(instance=participant)
    return render(request, 'survey_feedback.html', {'form': form})


def finish_survey(request):
    return render(request, 'finish_survey.html')
