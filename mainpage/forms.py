from django import forms
from mainpage.models import Question, Answer, User
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['title', 'detailed']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Title'}),
            'detailed': forms.Textarea(attrs={'placeholder': 'Your question'}),
        }
        error_messages = {
            'title': {'required': 'You must enter the title.'},
            'detailed': {'required': 'You must enter your question.'},
            'tags_text': {'You must enter at least one tag.'}
        }

    
    tags_text = forms.CharField(
        label='Tags',
        required=True,
        error_messages={'required': 'You must enter at least one tag.'},
        widget=forms.TextInput(attrs={'placeholder': 'Tags (e.g. golang, docker, kubernetes)'}),
        )
    
    def clean_title(self):
        title = self.cleaned_data.get('title').strip()
        if not title:
            raise forms.ValidationError('You must enter the title.')
        return title

    def clean_detailed(self):
        detailed = self.cleaned_data.get('detailed').strip()
        if not detailed:
            raise forms.ValidationError('You must enter your question.')
        return detailed
    
    def clean_tags_text(self):
        tags_text = self.cleaned_data.get('tags_text')
        tags = [t.strip() for t in tags_text.replace(';', ',').replace(' ', '').split(',') if t.strip()] # Заменяем все `;` на `,` и убираем пробелы чтобы по запятым разделить теги. Потом делим строку tags_text по запятым на подстроки(теги). Проходимся по тегам, если строка пустая, то скип, если нет, то норм.
        if not tags:
            raise forms.ValidationError('You must enter at least one tag.')
        return tags


class SettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'avatar']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Login'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'avatar': forms.FileInput(attrs={'accept': 'image/*'}),
        }
        error_messages = {
            'username': {'required': 'You must enter login.'},
            'email': {'required': 'You must enter email.'},
        }
    
    
    def clean_username(self):
        new_username = self.cleaned_data.get('username')

        if self.instance.pk and new_username:
            if User.objects.filter(username=new_username).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('This login is already taken by another user.')
        return new_username
    
    def clean_email(self):
        new_email = self.cleaned_data.get('email')

        if self.instance.pk and new_email:
            if User.objects.filter(username=new_email).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('This email is already taken by another user.')
        return new_email

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and avatar.size > 4 * 1024 * 1024: # 4Мб
            raise forms.ValidationError("Too big file (max size is 4Mb).")
        return avatar


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email'})
    )

    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )

    password2 = forms.CharField(
        label='Repeat password',
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Repeat your password'})
    )


    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'email', )
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Login'}),
        }
        error_messages = {
            'username': {'required': 'You must enter login.'},
            'password1': {'required': 'You must enter password.'},
            'password2': {'required': 'You must confirm your password.'},
            'email': {'required': 'You must enter email.'},
        }
    

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if username and User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This login is already taken by another user.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email and User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError('This email is already taken by another user.')
        return email
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        
        if password1:
            try:
                password_validation.validate_password(password1, user=None)
            except forms.ValidationError as e:
                raise forms.ValidationError(e.message)
        
        return password2

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text',]
        widgets = {
            'answer_text': forms.Textarea(attrs={'placeholder': 'Your answer'}),
        }
        error_messages = {
            'answer_text': {'required': 'You must enter your answer.'},
        }

    def clean_answer_text(self):
        answer_text = self.cleaned_data.get('answer_text').strip()
        if not answer_text:
            raise forms.ValidationError('You must enter your answer.')
        return answer_text