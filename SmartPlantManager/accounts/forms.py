from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from .models import Utente


class RegisterForm(UserCreationForm):
    username = forms.CharField(max_length=50, label="Username *")
    email = forms.EmailField(max_length=200, label="Email *")
    telegram = forms.CharField(max_length=50, label="Username Telegram", 
                               required=False, widget=forms.TextInput(attrs={'placeholder': '@username'}))

    class Meta:
        model = Utente
        fields = ['username', 'email', 'telegram', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['password1'].label = "Password *"
        self.fields['password2'].label = "Conferma password *"
        
        for f in self.fields.values():
            f.help_text = None

    def clean_password1(self):
        password = self.cleaned_data.get("password1")

        if len(password) < 8:
            raise ValidationError("La password deve contenere almeno 8 caratteri")
        
        if not any(c.isdigit() for c in password):
            raise ValidationError("La password deve contenere almeno un numero")
        
        if not any(c.isalpha() for c in password):
            raise ValidationError("La password deve contenere almeno una lettera")
        
        return password

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")

        if p1 and p2 and p1 != p2:
            raise ValidationError("Le password non coincidono")
        
        return p2


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=50)
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields.values():
            f.help_text = None

    error_messages = {
        "invalid_login": "Username o password errati",
        "inactive": "Questo account è inattivo.",
    }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Utente
        fields = ['email', 'telegram']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'La tua email'}),
            'telegram': forms.TextInput(attrs={'placeholder': '@username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rimuove gli help_text automatici di Django per mantenere il design pulito
        for field in self.fields.values():
            field.help_text = None