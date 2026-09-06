from django.core.management.base import BaseCommand
from django.db import transaction

from institutions.models import Institution, TechnicalCareer


SAMPLE_INSTITUTIONS = (
    {
        "name": "Instituto Tecnológico de Santo Domingo",
        "email": "contacto@itsd.example",
        "phone": "+1-809-555-0101",
        "address": "Av. Independencia 101, Santo Domingo",
        "careers": (
            (
                "Desarrollo de Software",
                "Formación en desarrollo de aplicaciones web y servicios backend.",
            ),
            (
                "Redes y Telecomunicaciones",
                "Diseño, configuración y mantenimiento de redes y sistemas de comunicación.",
            ),
            (
                "Administración de Sistemas",
                "Operación y soporte de servidores, sistemas operativos y servicios TI.",
            ),
        ),
    },
    {
        "name": "Centro Técnico del Cibao",
        "email": "info@centrotecnico-cibao.example",
        "phone": "+1-809-555-0102",
        "address": "Calle Restauración 45, Santiago de los Caballeros",
        "careers": (
            (
                "Soporte de Tecnologías de la Información",
                "Soporte técnico, mantenimiento de equipos y atención a usuarios.",
            ),
            (
                "Electrónica Industrial",
                "Instalación, diagnóstico y mantenimiento de sistemas electrónicos industriales.",
            ),
            (
                "Contabilidad Computarizada",
                "Gestión contable con herramientas digitales y sistemas administrativos.",
            ),
        ),
    },
    {
        "name": "Instituto Politécnico del Este",
        "email": "admisiones@ipe.example",
        "phone": "+1-809-555-0103",
        "address": "Av. La Romana 220, La Romana",
        "careers": (
            (
                "Diseño Gráfico Digital",
                "Creación de piezas visuales para medios impresos y digitales.",
            ),
            (
                "Marketing Digital",
                "Planificación de campañas, contenidos y analítica para canales digitales.",
            ),
            (
                "Gestión Administrativa",
                "Organización de procesos administrativos, documentación y servicio al cliente.",
            ),
        ),
    },
)


class Command(BaseCommand):
    help = "Agrega instituciones y carreras técnicas de ejemplo sin duplicar registros."

    @transaction.atomic
    def handle(self, *args, **options):
        institutions_created = 0
        careers_created = 0

        for institution_data in SAMPLE_INSTITUTIONS:
            careers = institution_data["careers"]
            institution, created = Institution.objects.get_or_create(
                name=institution_data["name"],
                defaults={
                    "email": institution_data["email"],
                    "phone": institution_data["phone"],
                    "address": institution_data["address"],
                    "is_active": True,
                },
            )
            institutions_created += int(created)

            for career_name, description in careers:
                _, created = TechnicalCareer.objects.get_or_create(
                    institution=institution,
                    name=career_name,
                    defaults={"description": description, "is_active": True},
                )
                careers_created += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Instituciones creadas: {institutions_created}. "
                f"Carreras creadas: {careers_created}."
            )
        )
