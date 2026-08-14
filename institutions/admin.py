from django.contrib import admin
from .models import Institution, TechnicalCareer, AcademicPeriod, InstitutionConfig

admin.site.register([Institution, TechnicalCareer, AcademicPeriod, InstitutionConfig])
