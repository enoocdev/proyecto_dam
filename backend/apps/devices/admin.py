from django.contrib import admin
from .models import Device 
from django.contrib.auth.admin import UserAdmin
from .models import User
# Register your models here.

admin.site.register(Device)
admin.site.register(User, UserAdmin)