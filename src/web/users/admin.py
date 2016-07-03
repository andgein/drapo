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

admin.site.register(models.User, UserAdmin)

