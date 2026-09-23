from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Administrador"
    INSTITUTION_ADMIN = "INSTITUTION_ADMIN", "Administrador Institucional"
    COORDINATOR = "COORDINATOR", "Coordinador de Pasantías"
    TUTOR = "TUTOR", "Tutor o Facilitador"
    STUDENT = "STUDENT", "Estudiante"
    COMPANY = "COMPANY", "Empresa"
    COMPANY_SUPERVISOR = "COMPANY_SUPERVISOR", "Supervisor Empresarial"

class User(AbstractUser):
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField(max_length=30, blank=True)
    institution = models.ForeignKey(
        "institutions.Institution", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="users"
    )
    company = models.ForeignKey(
        "companies.Company", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="users"
    )

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="audit_logs")
    action = models.CharField(max_length=100)
    entity = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
