from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *
from sorl.thumbnail.admin import AdminImageMixin


class ImageProductAdmin(AdminImageMixin, admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(Tier)
admin.site.register(ImageProduct)
admin.site.register(Plan)
admin.site.register(PlanThumbnailSetting)
admin.site.register(ExpiringToken)
