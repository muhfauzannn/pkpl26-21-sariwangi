from django import forms

from apps.candidates.models import Candidate


class VoteForm(forms.Form):
    candidate = forms.ModelChoiceField(
        queryset=Candidate.objects.filter(status=Candidate.Status.APPROVED),
        widget=forms.RadioSelect,
        error_messages={"required": "Pilih salah satu paslon."},
    )
