from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date
from .models import *
from django.forms.widgets import DateInput
import re
from django.contrib.auth.forms import AuthenticationForm
from datetime import timedelta

User = get_user_model()


class RegistrationForm(forms.Form):
    email = forms.EmailField(label="Email", required=True)
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Повторите пароль", widget=forms.PasswordInput)
    phone = forms.CharField(label="Телефон", required=False)
    birth_date = forms.DateField(
        help_text='Required. Format: YYYY-MM-DD',
        widget=DateInput(attrs={'type': 'date', 'min': '1900-01-01', 'required': 'required'})
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
            raise ValidationError("Неверный формат email")
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Этот email уже зарегистрирован")
        return email

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError("Пароли не совпадают")
        return p2

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if phone and not re.match(r'^\+375 \((17|29|33|44)\) \d{3}-\d{2}-\d{2}$', phone):
            raise ValidationError("Неверный формат телефона, ожидается +375 (29) 123-45-67")
        return phone

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        if age < 18:
            raise ValidationError("You must be at least 18 years old to register.")
        return birth_date

    def save(self):
        data = self.cleaned_data
        
        default_role = Role.objects.get(name='user') 
        user = CustomUser.objects.create_user(
            email=data['email'],
            password=data['password1'],
            phone=data.get('phone', ''),
            birth_date=data['birth_date'],
        )

        default_role = Role.objects.get(name='user') 
        user.roles.add(default_role)
        
        return user


class EmailAuthForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True})
    )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 10}),
        }
        
        
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['row', 'seat']
        widgets = {
            'row': forms.HiddenInput(),
            'seat': forms.HiddenInput(),
        }

class ScreeningForm(forms.ModelForm):
    class Meta:
        model = Screening
        fields = ['movie', 'hall', 'start_time', 'price']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }

    def clean(self):
        cleaned_data = super().clean()
        movie = cleaned_data.get('movie')
        hall = cleaned_data.get('hall')
        start_time = cleaned_data.get('start_time')

        if not all([movie, hall, start_time]):
            return cleaned_data

        # Проверка пересечения времени
        duration = timedelta(minutes=movie.duration)
        end_time = start_time + duration

        # Проверка наложения сеансов
        overlapping_screenings = Screening.objects.filter(
            hall=hall,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exclude(pk=self.instance.pk if self.instance else None)

        if overlapping_screenings.exists():
            raise forms.ValidationError(
                "Этот зал уже занят в указанное время. Выберите другое время или зал."
            )

        return cleaned_data
