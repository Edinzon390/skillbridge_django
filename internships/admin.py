from django.contrib import admin
from .models import (
    StudentProfile, Opportunity, Application, Internship,
    Activity, Evaluation, Evidence, InternshipCertificate
)
admin.site.register([
    StudentProfile, Opportunity, Application, Internship,
    Activity, Evaluation, Evidence, InternshipCertificate
])
