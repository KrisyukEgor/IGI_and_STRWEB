from django.views.generic import ListView, DetailView,TemplateView
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from .forms import *
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from django.views.generic.edit import FormMixin
from django.db.models import Sum, Avg
from django.contrib import messages
import requests
from django.db.models import Count
import json
import calendar
from datetime import datetime
from django.contrib.auth.decorators import login_required, user_passes_test

class MovieListView(ListView):
    model = Movie
    context_object_name = "movies"
    paginate_by = 10
    template_name = "movies_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['genres'] = Genre.objects.all()
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        genre = self.request.GET.get("genre")

        if genre:
            qs = qs.filter(genres__name__iexact=genre)
        return qs


class MovieDetailView(FormMixin, DetailView):
    model = Movie
    template_name = 'movie_details.html'
    context_object_name = 'movie'
    form_class = ReviewForm

    def get_success_url(self):
        return reverse('detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movie = self.get_object()
        context['reviews'] = movie.reviews.select_related('author').order_by('-created_at')
        context['review_form'] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not request.user.is_authenticated:
            return redirect('login')  # или отправить на форму входа

        form = self.get_form()
        if form.is_valid():
            review = form.save(commit=False)
            review.author = request.user
            review.movie = self.object
            review.save()
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)


class RegisterView(View):
    template_name = 'register.html'
    form_class = RegistrationForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            user = form.save()  
            login(request, user) 
            return redirect('profile')  

        return render(request, self.template_name, {'form': form})
    

class CustomLoginView(LoginView):
    form_class = EmailAuthForm
    template_name = 'login.html'

    def get_success_url(self):
        return reverse_lazy('profile')


class AddReviewView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'add_review.html'
    login_url = 'login'        
    raise_exception = False      

    def dispatch(self, request, *args, **kwargs):
        self.movie = get_object_or_404(Movie, pk=kwargs['movie_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.movie = self.movie
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('movie_detail', kwargs={'pk': self.movie.pk})

    def get_context_data(self, **context):
        ctx = super().get_context_data(**context)
        ctx['movie'] = self.movie
        return ctx




class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
    
        ctx['email'] = user.email
        ctx['phone'] = user.phone or '—'
        ctx['birth_date'] = user.birth_date.strftime('%d.%m.%Y') if user.birth_date else '—'
    
        return ctx


class BookingView(LoginRequiredMixin, DetailView):
    model = Screening
    template_name = 'booking.html'
    context_object_name = 'screening'
    form_class = TicketForm

    def get_object(self):
        # Убедимся, что зал загружается вместе с сеансом
        return get_object_or_404(
            Screening.objects.select_related('hall', 'movie'),
            pk=self.kwargs['screening_id']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        screening = self.object
        hall = screening.hall

        occupied = Ticket.objects.filter(
            screening=screening,
            status__in=['booked', 'paid']
        ).values_list('row', 'seat', 'status')

        paid_seats = []
        booked_seats = []
        status_dict = {}

        for row, seat, status in occupied:
            seat_id = f"{row}-{seat}"
            status_dict[seat_id] = status
            if status == 'paid':
                paid_seats.append(seat_id)
            else:  # 'booked'
                booked_seats.append(seat_id)

        context.update({
            'hall': hall,
            'paid_seats': paid_seats,
            'booked_seats': booked_seats,
            'seat_status_dict': status_dict,           
            'rows': range(1, hall.rows + 1),
            'seats': range(1, hall.seats_per_row + 1),
            'form': kwargs.get('form', self.form_class()),
        })


        print(f"Зал: {hall.name}, Ряды: {hall.rows}, Мест: {hall.seats_per_row}")
        print(f"Занято всего: {len(status_dict)} мест")
        return context


    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(request.POST)

        if form.is_valid():
            row = form.cleaned_data['row']
            seat = form.cleaned_data['seat']

            # Проверяем занятость места через словарь
            status = self.get_context_data()['seat_status_dict'].get((row, seat))

            if status == 'paid':
                form.add_error(None, "Это место уже оплачено")
            elif status == 'booked':
                form.add_error(None, "Это место уже забронировано")
            else:  # Если место свободно
                ticket = form.save(commit=False)
                ticket.user = request.user
                ticket.screening = self.object
                ticket.save()
                return redirect('payment', ticket_id=ticket.id)

        return self.render_to_response(self.get_context_data(form=form))
class ClientDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard_client.html"
    required_roles = ['client']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()

        # Получаем активные билеты (на будущие сеансы)
        active_tickets = Ticket.objects.filter(
            user=user,
            screening__start_time__gt=now,
            status__in=['booked', 'paid']
        ).select_related('screening', 'screening__movie', 'screening__hall')

        # Разделяем на оплаченные и неоплаченные
        paid_tickets = active_tickets.filter(status='paid')
        unpaid_tickets = active_tickets.filter(status='booked')

        # Билеты на прошедшие сеансы
        past_tickets = Ticket.objects.filter(
            user=user,
            screening__end_time__lt=now,
            status__in=['paid']
        ).select_related('screening', 'screening__movie', 'screening__hall')[:5]

        # Статистика
        ticket_stats = {
            'active': active_tickets.count(),
            'paid': paid_tickets.count(),
            'unpaid': unpaid_tickets.count(),
            'past': past_tickets.count(),
        }

        ctx.update({
            'paid_tickets': paid_tickets,
            'unpaid_tickets': unpaid_tickets,
            'past_tickets': past_tickets,
            'ticket_stats': ticket_stats,
            'now': now
        })
        return ctx


class PaymentView(DetailView):
    model = Ticket
    template_name = 'payment.html'
    context_object_name = 'ticket'
    pk_url_kwarg = 'ticket_id'

    def get_object(self):
        return get_object_or_404(
            Ticket.objects.select_related('screening', 'screening__movie'),
            pk=self.kwargs['ticket_id'],
            user=self.request.user,
            status='booked'
        )

    def post(self, request, *args, **kwargs):
        ticket = self.get_object()

        ticket.status = 'paid'
        ticket.payment_status = 'completed'
        ticket.save()

        return redirect('ticket_detail', ticket_id=ticket.id)

class TicketDetailView(DetailView):
    model = Ticket
    template_name = 'ticket_detail.html'
    context_object_name = 'ticket'
    pk_url_kwarg = 'ticket_id'

    def get_object(self):
        return get_object_or_404(
            Ticket.objects.select_related('screening', 'screening__movie'),
            pk=self.kwargs['ticket_id'],
            user=self.request.user
        )


class CustomLogoutView(LoginRequiredMixin, View):
    next_page = reverse_lazy('list')

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect(self.next_page)

class ScheduleView(ListView):
    model = Screening
    template_name = 'schedule.html'
    context_object_name = 'screenings'

    def get_queryset(self):
        movie_id = self.kwargs['movie_id']
        return Screening.objects \
            .select_related('movie', 'hall') \
            .filter(movie__id=movie_id)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['movie'] = Movie.objects.get(pk=self.kwargs['movie_id'])
        return ctx


def is_admin(user):
    return user.is_admin()

@login_required
@user_passes_test(is_admin)
def screening_create(request):
    if request.method == 'POST':
        form = ScreeningForm(request.POST)
        if form.is_valid():
            screening = form.save(commit=False)

            # Автоматический расчет времени окончания
            duration = screening.movie.duration
            screening.end_time = screening.start_time + timedelta(minutes=duration)

            screening.save()
            return redirect(reverse('screening_list', kwargs={'movie_id': screening.movie.id}))
    else:
        form = ScreeningForm()

    return render(request, 'screening_form.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def screening_update(request, pk):
    screening = get_object_or_404(Screening, pk=pk)

    if request.method == 'POST':
        form = ScreeningForm(request.POST, instance=screening)
        if form.is_valid():
            updated_screening = form.save(commit=False)

            duration = updated_screening.movie.duration
            updated_screening.end_time = updated_screening.start_time + timedelta(minutes=duration)

            updated_screening.save()
            return redirect(reverse('screening_list', kwargs={'movie_id': updated_screening.movie.id}))
    else:
        form = ScreeningForm(instance=screening)

    return render(request, 'screening_form.html', {
        'form': form,
        'screening': screening
    })

@login_required
@user_passes_test(is_admin)
def screening_delete(request, pk):
    screening = get_object_or_404(Screening, pk=pk)
    movie_id = screening.movie.id

    if request.method == 'POST':
        # Проверка на существующие билеты
        if screening.ticket_set.exists():
            messages.error(
                request,
                "Нельзя удалить сеанс, на который уже проданы билеты."
            )
        else:
            screening.delete()
            messages.success(request, "Сеанс успешно удален")

        return redirect(reverse('screening_list', kwargs={'movie_id': movie_id}))

    return render(request, 'screening_confirm_delete.html', {
        'screening': screening
    })

class SoldTicketsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Ticket
    template_name = 'sold_tickets.html'
    context_object_name = 'tickets'
    paginate_by = 50

    def test_func(self):
        return self.request.user.is_cashier() or self.request.user.is_admin()

    def get_queryset(self):
        return Ticket.objects.filter(status='paid') \
            .select_related('screening__movie',
                            'screening__hall',
                            'user') \
            .order_by('-screening__start_time')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Общая выручка
        total = self.get_queryset().aggregate(
            total_revenue=Sum('screening__price')
        )['total_revenue'] or 0
        ctx['total_revenue'] = total

        # Количество проданных билетов по фильмам
        tickets_per_movie = self.get_queryset().values('screening__movie__title') \
            .annotate(count=Count('id')).order_by('screening__movie__title')

        # Формируем списки меток и данных для диаграммы
        labels = [item['screening__movie__title'] for item in tickets_per_movie]
        data = [item['count'] for item in tickets_per_movie]

        # Преобразуем в JSON-строки для безопасной вставки в JS
        ctx['chart_labels'] = json.dumps(labels)
        ctx['chart_data'] = json.dumps(data)

        most_popular = tickets_per_movie.order_by('-count').first()
        ctx['most_popular_movie'] = most_popular['screening__movie__title'] if most_popular else None
        ctx['most_popular_movie_count'] = most_popular['count'] if most_popular else 0

        avg_price = self.get_queryset().aggregate(
                    avg=Avg('screening__price')
                )['avg'] or 0
        ctx['avg_ticket_price'] = round(avg_price, 2)        
        return ctx


class CompanyInfoView(TemplateView):
    template_name = 'company_info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = CompanyInfo.objects.first()
        return context


class NewsListView(ListView):
    model = NewsArticle
    template_name = 'news_list.html'
    context_object_name = 'articles'
    paginate_by = 10


class FAQListView(ListView):
    model = FAQEntry
    template_name = 'faq_list.html'
    context_object_name = 'faqs'

class ContactListView(ListView):
    model = ContactPerson
    template_name = 'contact_list.html'
    context_object_name = 'contacts'

class PrivacyPolicyView(TemplateView):
    template_name = 'privacy_policy.html'

class VacancyListView(ListView):
    model = Vacancy
    template_name = 'vacancy_list.html'
    context_object_name = 'vacancies'


class PromoCodeListView(ListView):
    model = PromoCode
    template_name = 'promo_list.html'
    context_object_name = 'promos'

    def get_queryset(self):
        return PromoCode.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        context['active_promos'] = PromoCode.objects.filter(
            is_active=True,
            valid_from__lte=today,
            valid_to__gte=today
        )
        context['archived_promos'] = PromoCode.objects.exclude(
            is_active=True,
            valid_from__lte=today,
            valid_to__gte=today
        )
        return context

class HomePageView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Последний фильм и новость
        context['last_movie'] = Movie.objects.order_by('-created_at').first()
        context['last_news'] = NewsArticle.objects.first()

        # Текущий месяц и год
        now = datetime.now()
        cal_text = calendar.TextCalendar().formatmonth(now.year, now.month)

        # Добавляем календарь в контекст
        context['calendar_text'] = cal_text

        return context

class CatFactView(TemplateView):
    template_name = 'cat_fact.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            response = requests.get('https://catfact.ninja/fact')
            if response.status_code == 200:
                data = response.json()
                context['cat_fact'] = data.get('fact')
            else:
                context['cat_fact'] = "Не удалось получить факт о кошках."
        except Exception:
            context['cat_fact'] = "Ошибка при запросе к API."
            
        return context


class AdviceView(TemplateView):
    template_name = 'advice.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            response = requests.get('https://api.adviceslip.com/advice')
            if response.status_code == 200:
                data = response.json()
                context['advice'] = data['slip']['advice']
            else:
                context['advice'] = "Не удалось получить совет."
        except Exception:
            context['advice'] = "Ошибка при запросе к API."
        return context