from django import forms

from .models import Participant


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['speciality', 'age', 'leading_hand', 'sex', 'languages',
                  'education']


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['email', 'feedback']