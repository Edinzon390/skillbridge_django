import os
import shutil
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Borra la base de datos sqlite3, limpia static/ de ejemplos, ejecuta migrate y pobla datos de ejemplo."

    def add_arguments(self, parser):
        parser.add_argument('--skip-static', action='store_true', dest='skip_static',
                            help='No borrar el contenido de STATICFILES_DIRS')
        parser.add_argument('--skip-populate', action='store_true', dest='skip_populate',
                            help='No crear datos de ejemplo después de migrar')

    def handle(self, *args, **options):
        skip_static = options.get('skip_static', False)
        skip_populate = options.get('skip_populate', False)

        # Only proceed for sqlite3 to avoid catastrophic deletes in other DBs
        default_db = settings.DATABASES.get("default", {})
        engine = default_db.get("ENGINE", "")
        db_name = default_db.get("NAME")

        if "sqlite3" not in engine.lower():
            self.stdout.write(self.style.ERROR("La base de datos no es sqlite3 — abortando para evitar pérdida accidental."))
            return

        # Delete the sqlite file if it exists
        if db_name and os.path.exists(str(db_name)):
            try:
                os.remove(str(db_name))
                self.stdout.write(self.style.SUCCESS(f"El archivo de base de datos eliminado: {db_name}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"No se pudo eliminar {db_name}: {e}"))
                return
        else:
            self.stdout.write("No se encontró archivo sqlite para eliminar — continuando.")

        # Clean example static content inside each STATICFILES_DIRS entry (unless skipped)
        if not skip_static:
            for static_dir in getattr(settings, "STATICFILES_DIRS", []):
                static_dir = str(static_dir)
                if os.path.isdir(static_dir):
                    try:
                        # Remove contents but keep the directory itself
                        for child in os.listdir(static_dir):
                            child_path = os.path.join(static_dir, child)
                            if os.path.isdir(child_path):
                                shutil.rmtree(child_path)
                            else:
                                os.remove(child_path)
                        self.stdout.write(self.style.SUCCESS(f"Contenido de static/ borrado en: {static_dir}"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error al limpiar {static_dir}: {e}"))
                else:
                    self.stdout.write(f"Static dir no existe: {static_dir} — se omitió.")
        else:
            self.stdout.write(self.style.WARNING('Omitiendo limpieza de static/ por flag --skip-static'))

        # Run migrations to recreate the database schema
        try:
            call_command("migrate", "--noinput")
            self.stdout.write(self.style.SUCCESS("Migraciones aplicadas correctamente."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al ejecutar migrate: {e}"))
            return

        # Populate sample content using helper functions below (unless skipped)
        if not skip_populate:
            try:
                self.stdout.write("Poblando datos de ejemplo...")
                self.populate_sample_data()
                self.stdout.write(self.style.SUCCESS("Poblado completado."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error al poblar datos: {e}"))
        else:
            self.stdout.write(self.style.WARNING('Omitiendo creación de datos de ejemplo por flag --skip-populate'))

    @transaction.atomic
    def populate_sample_data(self):
        User = get_user_model()

        # Institutions and careers
        from institutions.models import Institution, TechnicalCareer, AcademicPeriod, InstitutionConfig
        from companies.models import Company, Supervisor
        from internships.models import (
            StudentProfile, Opportunity, Application, Internship
        )
        from notifications.models import Notification

        # 1) Institution
        inst = Institution.objects.create(
            name="Institución Ejemplo",
            email="contacto@institucion.ej",
            phone="+1-555-000",
            address="Calle Falsa 123",
            is_active=True,
        )

        # Config
        InstitutionConfig.objects.create(
            institution=inst,
            required_hours=240,
            passing_score=70,
            allow_remote=True,
            rules={"nota": "Reglas de ejemplo"},
        )

        # Career
        career = TechnicalCareer.objects.create(
            institution=inst,
            name="Ingeniería de Software",
            description="Carrera de prueba",
            is_active=True,
        )

        # Academic period
        AcademicPeriod.objects.create(
            institution=inst,
            name="2026-1",
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=120)).date(),
            is_active=True,
        )

        # 2) Company
        comp = Company.objects.create(
            name="Empresa Ejemplo S.A.",
            legal_name="Empresa Ejemplo SA",
            tax_id="EJ123456",
            email="info@empresa.ej",
            phone="+1-555-111",
            address="Avenida Central 456",
            website="https://empresa.ej",
            is_validated=True,
            is_active=True,
        )

        # 3) Users: super admin, institution admin, student, company supervisor
        super_admin = User.objects.create_user(
            username="admin",
            email="admin@ejemplo",
            password="adminpass",
            role=User._meta.get_field("role").choices[0][0] if hasattr(User, "role") else "SUPER_ADMIN",
            is_superuser=True,
            is_staff=True,
        )

        inst_admin = User.objects.create_user(
            username="inst_admin",
            email="inst_admin@ejemplo",
            password="password",
            role=getattr(User, "role", None) and "INSTITUTION_ADMIN" or None,
        )
        inst_admin.institution = inst
        inst_admin.save()

        student_user = User.objects.create_user(
            username="student1",
            email="student1@ejemplo",
            password="password",
            role=getattr(User, "role", None) and "STUDENT" or None,
        )
        student_profile = StudentProfile.objects.create(
            user=student_user,
            institution=inst,
            career=career,
            student_code="STU-001",
            phone="+1-555-222",
            bio="Estudiante ejemplo",
            skills=["Python", "Django"],
            is_eligible=True,
        )

        supervisor_user = User.objects.create_user(
            username="supervisor1",
            email="sup1@empresa.ej",
            password="password",
            role=getattr(User, "role", None) and "COMPANY_SUPERVISOR" or None,
        )

        supervisor = Supervisor.objects.create(
            company=comp,
            user=supervisor_user,
            full_name="Supervisor Ejemplo",
            position="Jefe de Desarrollo",
            email="sup1@empresa.ej",
            phone="+1-555-333",
            is_active=True,
        )

        # 4) Opportunity and application
        opp = Opportunity.objects.create(
            institution=inst,
            company=comp,
            career=career,
            title="Pasante de Desarrollo",
            description="Pasantía en desarrollo backend",
            requirements=["Conocimientos en Python", "Interés en APIs"],
            vacancies=2,
            modality=Opportunity.Modality.REMOTE,
            deadline=timezone.now() + timedelta(days=30),
            status=Opportunity.Status.ACTIVE,
        )

        app = Application.objects.create(
            opportunity=opp,
            student=student_profile,
            message="Me interesa esta oportunidad",
            status=Application.Status.SENT,
        )

        # 5) Create an internship instance (simulate accepted application)
        internship = Internship.objects.create(
            application=app,
            student=student_profile,
            company=comp,
            supervisor=supervisor,
            start_date=(timezone.now() + timedelta(days=7)).date(),
            status=Internship.Status.PENDING,
            total_hours=0,
        )

        # 6) Notifications
        Notification.objects.create(
            user=student_user,
            title="Bienvenido",
            message="Cuenta creada y pasantía de ejemplo agregada.",
        )

        Notification.objects.create(
            user=super_admin,
            title="Sistema reiniciado",
            message="La base de datos fue reiniciada y datos de ejemplo creados.",
        )

        # Summary info output
        self.stdout.write(self.style.SUCCESS(
            f"Creado: Institution(id={inst.id}), Company(id={comp.id}), Opportunity(id={opp.id}), Internship(id={internship.id})"
        ))

        return
