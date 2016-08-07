import random

from django.shortcuts import render, redirect, Http404

from .forms import ParticipantForm, FeedbackForm
from .models import Participant, ContextSet, ContextGroup


def start_survey(request):
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save()
            return redirect('survey_step', str(participant.id), 0)
    else:
        form = ParticipantForm()
    return render(request, 'start_survey.html', {
        'form': form,
    })


def survey_step(request, participant_id, step):
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
    random.shuffle(contexts)
    return render(request, 'survey_step.html', {
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
