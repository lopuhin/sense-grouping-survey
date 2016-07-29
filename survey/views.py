from django.shortcuts import render, redirect

from .forms import TesteeForm
from .models import Testee, ContextSet


def start_survey(request):
    if request.method == 'POST':
        form = TesteeForm(request.POST)
        if form.is_valid():
            testee = form.save()
            return redirect('survey_step', str(testee.id), 0)
    else:
        form = TesteeForm()
    return render(request, 'start_survey.html', {
        'form': form,
    })


def survey_step(request, testee_id, step):
    testee = Testee.objects.get(pk=testee_id)
    contexts = ContextSet.objects.all()[int(step)]
    return render(request, 'survey_step.html', {
        'testee': testee,
        'contexts': contexts,
    })
