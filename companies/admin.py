from django.contrib import admin
from .models import Company, Supervisor
admin.site.register([Company, Supervisor])
