from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=250, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_validated = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Supervisor(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="supervisors")
    user = models.OneToOneField("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="supervisor_profile")
    full_name = models.CharField(max_length=200)
    position = models.CharField(max_length=150, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name
