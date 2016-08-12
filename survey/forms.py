from django import forms

from .models import Participant


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['profession', 'age', 'leading_hand', 'sex', 'languages',
                  'education']
        widgets = {
            'leading_hand': forms.Select(attrs={'class': 'input'}),
            'education': forms.Select(attrs={'class': 'input'}),
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['email', 'feedback']