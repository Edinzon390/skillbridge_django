from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

class StudentProfile(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="student_profile")
    institution = models.ForeignKey("institutions.Institution", on_delete=models.CASCADE, related_name="students")
    career = models.ForeignKey("institutions.TechnicalCareer", on_delete=models.PROTECT, related_name="students")
    student_code = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)
    cv = models.FileField(upload_to="students/cv/", blank=True, null=True)
    portfolio = models.FileField(upload_to="students/portfolio/", blank=True, null=True)
    is_eligible = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Opportunity(models.Model):
    class Modality(models.TextChoices):
        PRESENTIAL = "PRESENTIAL", "Presencial"
        REMOTE = "REMOTE", "Remota"
        HYBRID = "HYBRID", "Híbrida"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activa"
        CLOSED = "CLOSED", "Cerrada"
        PAUSED = "PAUSED", "Pausada"
        CANCELLED = "CANCELLED", "Cancelada"

    institution = models.ForeignKey("institutions.Institution", on_delete=models.CASCADE, related_name="opportunities")
    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="opportunities")
    career = models.ForeignKey("institutions.TechnicalCareer", on_delete=models.PROTECT, related_name="opportunities")
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.JSONField(default=list, blank=True)
    vacancies = models.PositiveIntegerField(default=1)
    modality = models.CharField(max_length=20, choices=Modality.choices)
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.company.is_validated:
            raise ValidationError("La empresa debe estar validada antes de publicar oportunidades.")
        if not self.deadline:
            raise ValidationError("Toda oportunidad debe tener fecha límite.")

class Application(models.Model):
    class Status(models.TextChoices):
        SENT = "SENT", "Enviada"
        REVIEW = "REVIEW", "En revisión"
        ACCEPTED = "ACCEPTED", "Aceptada"
        REJECTED = "REJECTED", "Rechazada"

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="applications")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="applications")
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SENT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["opportunity", "student"], name="unique_student_opportunity")
        ]

    def clean(self):
        if not self.student.is_eligible:
            raise ValidationError("Solo estudiantes elegibles pueden aplicar.")
        if self.opportunity.status != Opportunity.Status.ACTIVE:
            raise ValidationError("Solo puedes aplicar a oportunidades activas.")
        if self.opportunity.deadline < timezone.now():
            raise ValidationError("La fecha límite de esta oportunidad ya venció.")
        active = Internship.objects.filter(
            student=self.student,
            status=Internship.Status.IN_PROGRESS
        ).exists()
        if active:
            raise ValidationError("El estudiante ya tiene una pasantía activa.")

class Internship(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        IN_PROGRESS = "IN_PROGRESS", "En proceso"
        PAUSED = "PAUSED", "Pausada"
        FINISHED = "FINISHED", "Finalizada"
        CANCELLED = "CANCELLED", "Cancelada"

    application = models.OneToOneField(Application, on_delete=models.PROTECT, related_name="internship")
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name="internships")
    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="internships")
    supervisor = models.ForeignKey("companies.Supervisor", on_delete=models.PROTECT, related_name="internships")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_hours = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def can_finish(self):
        return hasattr(self, "evaluation")

class Activity(models.Model):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name="activities")
    date = models.DateField(default=timezone.now)
    description = models.TextField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    validated = models.BooleanField(default=False)
    validated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="activities_created")
    created_at = models.DateTimeField(auto_now_add=True)

class Evaluation(models.Model):
    internship = models.OneToOneField(Internship, on_delete=models.CASCADE, related_name="evaluation")
    score = models.DecimalField(max_digits=5, decimal_places=2)
    criteria = models.JSONField(default=dict, blank=True)
    comments = models.TextField(blank=True)
    result = models.CharField(max_length=30, default="PENDING")
    evaluated_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    evaluated_at = models.DateTimeField(auto_now_add=True)

class Evidence(models.Model):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name="evidences")
    uploaded_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    file = models.FileField(upload_to="internships/evidences/")
    description = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class InternshipCertificate(models.Model):
    internship = models.OneToOneField(Internship, on_delete=models.CASCADE, related_name="certificate")
    certificate_number = models.CharField(max_length=100, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="internships/certificates/", blank=True, null=True)
