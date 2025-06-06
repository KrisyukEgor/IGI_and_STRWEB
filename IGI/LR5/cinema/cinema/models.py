from django.db import models
from django.contrib.auth.models import AbstractUser, Permission
from django.conf import settings
from .managers import CustomUserManager
from django.utils import timezone

class Genre(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class Movie(models.Model):
    title = models.CharField(max_length=100, verbose_name="Название")
    country = models.CharField(max_length=100, verbose_name="Страна")
    duration = models.PositiveIntegerField(verbose_name="Длительность (мин)")
    budget = models.BigIntegerField(null=True, blank=True, verbose_name="Бюджет")
    description = models.TextField(blank=True, verbose_name="Описание")
    rating = models.FloatField(default=0.0, verbose_name="Рейтинг")
    poster = models.ImageField(upload_to='posters/', blank=True,null=True,verbose_name="Постер")
    genres = models.ManyToManyField(Genre, related_name="movies", verbose_name="Жанры")

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
            return self.title

class Role(models.Model):
    ROLES = (
        ('cashier', 'Кассир'),
        ('user', 'Обычный пользователь'),
        ('admin', 'Администратор'),
    )

    name = models.CharField(max_length=100, choices=ROLES, unique=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name='Права доступа',
        blank=True,
        related_name='roles'
    )

    def __str__(self):
        return self.get_name_display()


class CustomUser(AbstractUser):
    
    roles = models.ManyToManyField(
        Role,
        verbose_name='Роли',
        blank=True,
        related_name='users'
    )

    username = None
    email = models.EmailField(unique=True, verbose_name='Email')
    phone = models.CharField( max_length=20, verbose_name="Телефон", blank=True, null=True )
    birth_date = models.DateField(null=True, blank = True,verbose_name='')
    
    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = []     

    objects = CustomUserManager()

    def has_perm(self, perm, obj=None):
        if self.is_superuser:
            return True
        return super().has_perm(perm, obj) or any(
            role.permissions.filter(codename=perm.split('.')[-1]).exists()
            for role in self.roles.all()
        )

    def is_admin(self):
        return self.is_superuser or self.roles.filter(name='admin').exists()

    def is_cashier(self):
        return self.roles.filter(name='cashier').exists()

    def get_tickets(self):
        return self.ticket_set.all()

    def get_active_tickets(self):
        return self.ticket_set.exclude(status='canceled')

    def get_pending_payment_tickets(self):
        return self.ticket_set.filter(
            status='booked',
            payment_status='pending'
        )

    def get_paid_tickets(self):
        return self.ticket_set.filter(
            status='paid',
            payment_status='completed'
        )
class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 11)]  

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор'
    )
    movie = models.ForeignKey(
        'cinema.Movie',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Фильм'
    )
    text = models.TextField("Текст отзыва")
    rating = models.PositiveSmallIntegerField("Оценка", choices=RATING_CHOICES)
    created_at = models.DateTimeField("Дата добавления", auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.email} — {self.movie.title} ({self.rating}/10)"


class Hall(models.Model):
    name = models.CharField("Название зала", max_length=100)
    rows = models.PositiveIntegerField("Количество рядов")
    seats_per_row = models.PositiveIntegerField("Мест в ряду")
    description = models.TextField("Описание зала", blank=True)

    def __str__(self):
        return f"{self.name} ({self.rows}x{self.seats_per_row})"

    class Meta:
        verbose_name = "Зал"
        verbose_name_plural = "Залы"
        
class Screening(models.Model):
    movie = models.ForeignKey(
        'Movie',
        on_delete=models.CASCADE,
        verbose_name="Фильм"
    )
    hall = models.ForeignKey(
        Hall,
        on_delete=models.CASCADE,
        verbose_name="Зал"
    )
    start_time = models.DateTimeField("Время начала")
    end_time = models.DateTimeField("Время окончания")
    price = models.DecimalField(
        "Цена билета",
        max_digits=8,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.movie} - {self.start_time}"

    class Meta:
        verbose_name = "Сеанс"
        verbose_name_plural = "Сеансы"
        ordering = ['start_time']



class Ticket(models.Model):

    STATUS_CHOICES = (
        ('booked', 'Забронирован'),
        ('paid', 'Оплачен'),
        ('canceled', 'Отменен'),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    screening = models.ForeignKey(
        Screening,
        on_delete=models.CASCADE,
        verbose_name="Сеанс"
    )
    row = models.PositiveIntegerField("Ряд")
    seat = models.PositiveIntegerField("Место")
    status = models.CharField(
        "Статус",
        max_length=10,
        choices=STATUS_CHOICES,
        default='booked'
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    payment_id = models.CharField(
        "ID платежа",
        max_length=100,
        blank=True,
        null=True
    )
    payment_status = models.CharField(
        "Статус платежа",
        max_length=20,
        choices=(
            ('pending', 'Ожидает оплаты'),
            ('completed', 'Оплачен'),
            ('failed', 'Ошибка оплаты'),
        ),
        default='pending'
    )
    
    class Meta:
        verbose_name = "Билет"
        verbose_name_plural = "Билеты"
        unique_together = [['screening', 'row', 'seat']]

    def __str__(self):
        return f"Билет на {self.screening} ({self.row} ряд, {self.seat} место)"


class CompanyInfo(models.Model):
    name = models.CharField("Название компании", max_length=255)
    description = models.TextField("Описание", blank=True)
    logo = models.ImageField("Логотип", upload_to='company/', blank=True, null=True)
    video = models.FileField("Видео о компании", upload_to='company/videos/', blank=True, null=True)
    history = models.TextField("История по годам (можно JSON или просто текст)", blank=True)

    requisites = models.TextField("Реквизиты", help_text="Например: ИНН, ОГРН, юр. адрес и пр.", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Информация о компании"
        verbose_name_plural = "Информация о компании"


class NewsArticle(models.Model):
    title = models.CharField("Заголовок", max_length=200)
    summary = models.CharField("Краткое содержание", max_length=300)
    image = models.ImageField("Картинка", upload_to="news_images/")
    created_at = models.DateTimeField("Дата публикации", auto_now_add=True)

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class FAQEntry(models.Model):
    question = models.CharField("Вопрос", max_length=300)
    answer = models.TextField("Ответ")
    created_at = models.DateTimeField("Дата добавления", auto_now_add=True)

    class Meta:
        verbose_name = "Термин / Вопрос"
        verbose_name_plural = "Словарь терминов / FAQ"
        ordering = ['-created_at']

    def __str__(self):
        return self.question

class ContactPerson(models.Model):
    name = models.CharField("ФИО", max_length=100)
    photo = models.ImageField("Фото", upload_to="contact_photos/")
    position = models.CharField("Должность / Задачи", max_length=200)
    phone = models.CharField("Телефон", max_length=30, blank=True)
    email = models.EmailField("Почта", blank=True)

    class Meta:
        verbose_name = "Контактное лицо"
        verbose_name_plural = "Контакты"
        ordering = ['name']

    def __str__(self):
        return self.name

class Vacancy(models.Model):
    title = models.CharField("Название вакансии", max_length=100)
    description = models.TextField("Описание вакансии")
    published_at = models.DateField("Дата публикации", auto_now_add=True)

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ['-published_at']

    def __str__(self):
        return self.title

class PromoCode(models.Model):
    code = models.CharField("Промокод", max_length=50, unique=True)
    description = models.TextField("Описание", blank=True)
    discount_percent = models.PositiveIntegerField("Скидка (%)")
    valid_from = models.DateField("Действует с")
    valid_to = models.DateField("Действует до")
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"
        ordering = ['-valid_to']

    def __str__(self):
        return self.code

    def is_currently_active(self):
        today = timezone.now().date()
        return self.is_active and self.valid_from <= today <= self.valid_to