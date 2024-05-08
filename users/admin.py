from django.contrib import admin

from .models import User, Customers

admin.site.register(User)
admin.site.register(Customers)

# Register your models here.
