from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from companies.models import Company
from institutions.models import Institution, TechnicalCareer
from internships.models import Opportunity


SAMPLE_OPPORTUNITIES = (
    {
        "company": {
            "name": "Caribe Digital Solutions",
            "legal_name": "Caribe Digital Solutions SRL",
            "tax_id": "CDS-001",
            "email": "talento@caribedigital.example",
            "phone": "+1-809-555-0201",
            "address": "Av. Winston Churchill 180, Santo Domingo",
            "website": "https://caribedigital.example",
        },
        "title": "Pasante de Desarrollo Web",
        "career": "Desarrollo de Software",
        "description": "Apoyo al equipo de desarrollo en aplicaciones web con Python y JavaScript.",
        "requirements": ["Python básico", "HTML y CSS", "Trabajo en equipo"],
        "vacancies": 2,
        "modality": Opportunity.Modality.HYBRID,
    },
    {
        "company": {
            "name": "Conecta Redes Dominicana",
            "legal_name": "Conecta Redes Dominicana SRL",
            "tax_id": "CRD-002",
            "email": "rrhh@conectaredes.example",
            "phone": "+1-809-555-0202",
            "address": "Calle El Sol 75, Santiago de los Caballeros",
            "website": "https://conectaredes.example",
        },
        "title": "Pasante de Soporte y Redes",
        "career": "Redes y Telecomunicaciones",
        "description": "Soporte en la instalación, documentación y monitoreo de redes empresariales.",
        "requirements": ["Fundamentos de redes", "Atención a usuarios", "Disponibilidad presencial"],
        "vacancies": 1,
        "modality": Opportunity.Modality.PRESENTIAL,
    },
    {
        "company": {
            "name": "Innovación Empresarial del Este",
            "legal_name": "Innovación Empresarial del Este SRL",
            "tax_id": "IEE-003",
            "email": "oportunidades@innovacioneste.example",
            "phone": "+1-809-555-0203",
            "address": "Av. Francisco Alberto Caamaño 40, La Romana",
            "website": "https://innovacioneste.example",
        },
        "title": "Pasante de Marketing Digital",
        "career": "Marketing Digital",
        "description": "Colaboración en campañas digitales, creación de contenidos y análisis de resultados.",
        "requirements": ["Redacción de contenidos", "Redes sociales", "Manejo básico de métricas"],
        "vacancies": 2,
        "modality": Opportunity.Modality.REMOTE,
    },
    {
        "company": {
            "name": "Servicios TI del Caribe",
            "legal_name": "Servicios TI del Caribe SRL",
            "tax_id": "STC-004",
            "email": "empleos@serviciosti.example",
            "phone": "+1-809-555-0204",
            "address": "Av. 27 de Febrero 310, Santo Domingo",
            "website": "https://serviciosti.example",
        },
        "title": "Pasante de Administración de Sistemas",
        "career": "Administración de Sistemas",
        "description": "Apoyo en la administración de servidores, respaldos y monitoreo de servicios.",
        "requirements": ["Sistemas operativos", "Conceptos de servidores", "Organización"],
        "vacancies": 1,
        "modality": Opportunity.Modality.HYBRID,
    },
    {
        "company": {
            "name": "Manufacturas del Cibao",
            "legal_name": "Manufacturas del Cibao SRL",
            "tax_id": "MDC-005",
            "email": "talento@manufacturascibao.example",
            "phone": "+1-809-555-0205",
            "address": "Zona Industrial Norte, Santiago de los Caballeros",
            "website": "https://manufacturascibao.example",
        },
        "title": "Pasante de Electrónica Industrial",
        "career": "Electrónica Industrial",
        "description": "Soporte al mantenimiento preventivo y diagnóstico de equipos industriales.",
        "requirements": ["Lectura de diagramas", "Seguridad industrial", "Interés técnico"],
        "vacancies": 1,
        "modality": Opportunity.Modality.PRESENTIAL,
    },
    {
        "company": {
            "name": "Estudio Visual Caribe",
            "legal_name": "Estudio Visual Caribe SRL",
            "tax_id": "EVC-006",
            "email": "hola@estudiovisual.example",
            "phone": "+1-809-555-0206",
            "address": "Calle Duarte 88, La Romana",
            "website": "https://estudiovisual.example",
        },
        "title": "Pasante de Diseño Gráfico",
        "career": "Diseño Gráfico Digital",
        "description": "Creación de piezas gráficas para campañas comerciales y redes sociales.",
        "requirements": ["Portafolio básico", "Principios de diseño", "Creatividad"],
        "vacancies": 1,
        "modality": Opportunity.Modality.REMOTE,
    },
)


class Command(BaseCommand):
    help = "Agrega empresas y oportunidades de ejemplo sin duplicar registros."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("seed_institutions", verbosity=0)
        opportunities_created = 0
        companies_created = 0
        deadline = timezone.now() + timedelta(days=45)

        for opportunity_data in SAMPLE_OPPORTUNITIES:
            company_data = opportunity_data["company"]
            company, created = Company.objects.get_or_create(
                name=company_data["name"],
                defaults={
                    **{key: value for key, value in company_data.items() if key != "name"},
                    "is_validated": True,
                    "is_active": True,
                },
            )
            companies_created += int(created)

            career = TechnicalCareer.objects.filter(
                name=opportunity_data["career"],
                institution__is_active=True,
            ).select_related("institution").first()
            if career is None:
                self.stdout.write(
                    self.style.ERROR(
                        f"No se encontró la carrera de ejemplo: {opportunity_data['career']}"
                    )
                )
                raise RuntimeError("No se puede crear la oportunidad sin una carrera válida.")

            _, created = Opportunity.objects.get_or_create(
                company=company,
                institution=career.institution,
                career=career,
                title=opportunity_data["title"],
                defaults={
                    "description": opportunity_data["description"],
                    "requirements": opportunity_data["requirements"],
                    "vacancies": opportunity_data["vacancies"],
                    "modality": opportunity_data["modality"],
                    "deadline": deadline,
                    "status": Opportunity.Status.ACTIVE,
                },
            )
            opportunities_created += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Empresas creadas: {companies_created}. "
                f"Oportunidades creadas: {opportunities_created}."
            )
        )
