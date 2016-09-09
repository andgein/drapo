from django.contrib import admin
import django.contrib.auth.admin as auth_admin

from hijack_admin.admin import HijackUserAdminMixin

from . import models


class UserAdmin(HijackUserAdminMixin, auth_admin.UserAdmin):
    list_display = ('id', 'username', 'first_name', 'last_name', 'email',
                    'is_superuser', 'is_staff',
                    'hijack_field',
                    )

    list_filter = ('is_superuser', 'is_staff', )

    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email',
    )

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', )}),
    )

admin.site.register(models.User, UserAdmin)


class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'token', 'is_confirmed')

    list_filter = ('is_confirmed', )

    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'user__email', 'token')

admin.site.register(models.EmailConfirmation, EmailConfirmationAdmin)

