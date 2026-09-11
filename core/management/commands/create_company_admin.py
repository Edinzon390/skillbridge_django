from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea el usuario administrador de empresas para las oportunidades de ejemplo."

    username = "empresa_admin"
    email = "empresa_admin@skillbridge.local"
    password = "EmpresaDemo2026!"

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=self.username,
            defaults={
                "email": self.email,
                "role": "COMPANY",
                "is_staff": True,
                "is_active": True,
            },
        )
        user.email = self.email
        user.role = "COMPANY"
        user.is_staff = True
        user.is_active = True
        user.set_password(self.password)
        user.save()

        action = "creado" if created else "actualizado"
        self.stdout.write(
            self.style.SUCCESS(
                f"Usuario {action}: {self.username} / {self.password}"
            )
        )
