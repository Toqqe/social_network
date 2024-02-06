from django import forms

from django.contrib.auth.models import User
from core.models import Profile
from django.core.exceptions import ValidationError


class UpdateUserForm(forms.ModelForm):
    username = forms.CharField(max_length=30, required=True)
    email = forms.CharField(required=True)

    username.widget.attrs['class'] = "form-control"
    email.widget.attrs['class'] = "form-control"

    class Meta:
        model = User
        fields = ['username', 'email']
            

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(UpdateUserForm, self).__init__(*args, **kwargs)


    def clean_email(self):
            email = self.cleaned_data["email"]
            users = User.objects.filter(email__iexact=email).exclude(username__iexact=self.user)

            if users:
                raise forms.ValidationError('A user with that email already exists.')
            return email.lower()
    


class UpdateProfileform(forms.ModelForm):
    profile_img = forms.ImageField(required=False, widget=forms.FileInput)
    description = forms.Textarea()

    class Meta:
        model = Profile
        fields = ['description', 'profile_img']



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].widget.attrs.update({'class':'description-field', 'placeholder':'Add something about You!', 'oninput':'auto_grow(this)'})
        self.fields['profile_img'].widget.attrs.update({'class':'profile_img btn btn-dark', 'onchange':'loadFile(event)'}) 
