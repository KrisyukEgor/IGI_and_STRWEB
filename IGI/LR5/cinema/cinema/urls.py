from django.contrib import admin
from django.urls import path
from .views import  *
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', MovieListView.as_view(), name = "list"),
    path('home', HomePageView.as_view(), name='home'),
    path('<int:pk>/', MovieDetailView.as_view(), name='detail'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path( 'movie/<int:movie_id>/review/',AddReviewView.as_view(), name='add_review'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('movies/<int:movie_id>/schedule/', ScheduleView.as_view(), name='screening_list'),
    path('booking/<int:screening_id>/', BookingView.as_view(), name='booking'),
    path('dashboard/client/', ClientDashboardView.as_view(), name='dashboard_client'),
    path('payment/<int:ticket_id>/', PaymentView.as_view(), name='payment'),
    path('ticket/<int:ticket_id>/', TicketDetailView.as_view(), name='ticket_detail'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('screenings/add/', screening_create, name='screening_add'),
    path('screenings/<int:pk>/edit/', screening_update, name='screening_edit'),
    path('screenings/<int:pk>/delete/', screening_delete, name='screening_delete'),
    path('cashier/sold-tickets/', SoldTicketsView.as_view(), name='sold_tickets'),
    path('about/', CompanyInfoView.as_view(), name='company_info'),
    path('news/', NewsListView.as_view(), name='news_list'),
    path('faq/', FAQListView.as_view(), name='faq_list'),
    path('contacts/', ContactListView.as_view(), name='contact_list'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('vacancies/', VacancyListView.as_view(), name='vacancy_list'),
    path('promocodes/', PromoCodeListView.as_view(), name='promo_list'),

    path('cat-fact/', CatFactView.as_view(), name='cat_fact'),
    path('advice/', AdviceView.as_view(), name='advice'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)