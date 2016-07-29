from django import forms

from .models import Testee


class TesteeForm(forms.ModelForm):
    class Meta:
        model = Testee
        exclude = []