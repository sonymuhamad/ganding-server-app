from django.contrib.auth.forms import UserCreationForm
from django import forms

from django.contrib.auth.models import User,Group


class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    group = forms.ModelChoiceField(queryset=Group.objects.all(),required=True)

    def save(self,commit = True):
        user = super().save(commit)
        user.groups.add(self.cleaned_data['group'])

    class Meta:
        model = User
        fields = ['username','email','password1','password2','group']


