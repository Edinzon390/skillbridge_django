from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Agrega instituciones, carreras y una cuenta empresarial de ejemplo."

    def handle(self, *args, **options):
        call_command("seed_institutions")
        call_command("create_company_admin")
        self.stdout.write(
            self.style.SUCCESS("Datos de demostración creados o actualizados correctamente.")
        )
