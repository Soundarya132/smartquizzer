from django import forms
from .models import Registration, Mcq

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ["first_name", "last_name", "email", "password", "contact", "gender"]
        widgets = {
            "password": forms.PasswordInput(),
        }

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class MCQUploadForm(forms.Form):
    topic_name = forms.CharField(max_length=100)
    sub_topic_name = forms.CharField(max_length=100)
    difficulty_level = forms.CharField(max_length=50)
    document = forms.FileField()
