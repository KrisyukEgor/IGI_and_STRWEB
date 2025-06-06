# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import *

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'get_roles', 'is_staff', 'is_active')
    list_filter = ('roles', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('roles', 'groups', 'user_permissions')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone', 'birth_date')}),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'roles',
                'groups',
                'user_permissions'
            ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'phone',
                'birth_date',
                'is_staff',
                'is_active',
                'roles'
            ),
        }),
    )

    def get_roles(self, obj):
        return ", ".join([r.name for r in obj.roles.all()])
    get_roles.short_description = _('Roles')

admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(Review)



@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'permissions_count')
    filter_horizontal = ('permissions',)

    def permissions_count(self, obj):
        return obj.permissions.count()
    permissions_count.short_description = _('Permissions count')


@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    list_display = ('name', 'rows', 'seats_per_row', 'total_seats')
    search_fields = ('name',)

    def total_seats(self, obj):
        return obj.rows * obj.seats_per_row
    total_seats.short_description = "Всего мест"

@admin.register(Screening)
class ScreeningAdmin(admin.ModelAdmin):
    list_display = ('movie', 'hall', 'start_time', 'end_time', 'price')
    list_filter = ('hall', 'start_time')
    raw_id_fields = ('movie', 'hall')  
    date_hierarchy = 'start_time'

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('user', 'screening', 'row', 'seat', 'status')
    list_filter = ('status', 'screening')
    search_fields = ('user__email', 'screening__movie__title')

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")

@admin.register(FAQEntry)
class FAQEntryAdmin(admin.ModelAdmin):
    list_display = ('question', 'created_at')
    search_fields = ('question', 'answer')

@admin.register(ContactPerson)
class ContactPersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'phone', 'email')
    search_fields = ('name', 'position')

@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at')
    search_fields = ('title',)

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'valid_from', 'valid_to', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code',)

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'summary')
    ordering = ('-created_at',)


