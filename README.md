# SkillBridge – Plataforma Inteligente de Vinculación para Pasantías Técnicas

Starter backend en Django + Django REST Framework basado en las especificaciones del proyecto.

## Requisitos
- Python 3.12+
- Django 5.x
- Django REST Framework
- django-filter
- Simple JWT
- Pillow

## Instalación

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Estructura

- `accounts`: usuarios, roles y bitácora.
- `institutions`: instituciones, carreras y períodos.
- `companies`: empresas y supervisores.
- `internships`: oportunidades, postulaciones, pasantías, actividades, evaluaciones y evidencias.
- `notifications`: notificaciones.
- `core`: configuración compartida y permisos.

## Roles

SUPER_ADMIN, INSTITUTION_ADMIN, COORDINATOR, TUTOR, STUDENT, COMPANY, COMPANY_SUPERVISOR.

## Reglas de negocio principales implementadas

1. Solo estudiantes elegibles pueden postular.
2. Una empresa debe estar validada para publicar oportunidades.
3. Un estudiante no puede tener más de una pasantía activa.
4. Las horas registradas deben ser validadas por el supervisor empresarial.
5. Una pasantía no puede finalizar sin evaluación.
6. Toda oportunidad debe tener fecha límite.
7. El coordinador institucional puede supervisar las pasantías de su institución.
8. Las actividades quedan registradas en bitácora.

Las funciones futuras de IA/matching, QR, geolocalización, firma digital, bolsa de empleo, app móvil y dashboard nacional quedan preparadas como extensiones y no forman parte del MVP.
