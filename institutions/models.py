from django.db import models

class Institution(models.Model):
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to="institutions/logos/", blank=True, null=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TechnicalCareer(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="careers")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("institution", "name")

    def __str__(self):
        return self.name

class AcademicPeriod(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="periods")
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class InstitutionConfig(models.Model):
    institution = models.OneToOneField(Institution, on_delete=models.CASCADE, related_name="config")
    required_hours = models.PositiveIntegerField(default=0)
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, default=70)
    allow_remote = models.BooleanField(default=True)
    rules = models.JSONField(default=dict, blank=True)
