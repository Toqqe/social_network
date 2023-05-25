from django import forms
from .models import Comment, Post, Profile, Comment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError
import os

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=30, required=True, error_messages={
        "required": "Your name must not be empty!",
        "max_length": "Please enter a shorter name!"
    })
    password = forms.CharField(widget=forms.PasswordInput())
    username.widget.attrs['class'] = "form-control"
    password.widget.attrs['class'] = "form-control"

def validate_email(value):
    if User.objects.filter(email = value).exists():
        raise ValidationError( (f"{value} is taken."), params = {'value':value})


class RegisterForm(UserCreationForm):

    username = forms.RegexField(max_length=30, required=True,regex=r"^[\w.@+-]+$", 
                                error_messages={
                                    'invalid': ("This value may contain only letters, numbers and " "@/./+/-/_ characters.")})

    password1 = forms.CharField(label="Password", required=True ,widget=forms.PasswordInput())
    password2 = forms.CharField(label="Password confirmation", required=True,widget=forms.PasswordInput(),help_text=("Enter the same password as above, for verification."))

    email = forms.CharField(required=True, validators= [validate_email])

    username.widget.attrs['class'] = "form-control"
    password1.widget.attrs['class'] = "form-control"
    password2.widget.attrs['class'] = "form-control"
    email.widget.attrs['class'] = "form-control"

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class AddPost(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'image']
        labels = {
            'content': 'Content',
        }
        error_messages = {
            'content': {
                'required': ("Please let us know what you want to write!"),
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'class': 'title-field', 'placeholder':'Title', 'oninput':'auto_grow(this)'})
        self.fields['content'].widget.attrs.update({'class':'post-field', 'placeholder':'Add something!', 'oninput':'auto_grow_content(this)'})
        self.fields['image'].widget.attrs.update({'class':'image-field btn btn-dark', 'onchange':'loadFile(event)'})

class UpdatePost(forms.ModelForm):
    title = forms.CharField(max_length=80, required=False)
    content = forms.Textarea()
    image = forms.ImageField(label="Upload New Image: ", widget=forms.FileInput, required=False)
    remove_photo = forms.BooleanField(required=False)


    class Meta:
        model = Post
        fields = ['title', 'content', 'image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'class': 'form-control title-field', 'placeholder':'Title', 'oninput':'auto_grow(this)'})
        self.fields['content'].widget.attrs.update({'class':'content-field', 'placeholder':'Add something!', 'oninput':'auto_grow_content(this)'})
        self.fields['image'].widget.attrs.update({'class':'image-field btn btn-dark','onchange':'loadFile(event)' }) ## 'onchange':'loadFile(event)'

        self.fields['remove_photo'].widget.attrs.update({'class':'btn btn-dark', 'style':'height:1rem; width:1rem; margin-bottom:1rem;'}) ## 'onchange':'loadFile(event)'

    def save(self, commit=True):
        instance = super(UpdatePost, self).save(commit=False)
        if self.cleaned_data.get('remove_photo'):
            instance.image = ""
        if commit:
            instance.save()

        return instance
    

class CommentForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={'class':'form-control comment-area','cols':'40','rows':'1', 'type':'text', 'oninput':'auto_grow_content(this)'}), label='', max_length=400)
    class Meta:
        model = Comment
        fields = ['text']

