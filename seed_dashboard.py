from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

# Superuser
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={'email': 'admin@example.com', 'role': 'SUPER_ADMIN'}
)
if created:
    admin.set_password('adminpass')
    admin.is_superuser = True
    admin.is_staff = True
    admin.save()

# Institutions and careers
from institutions.models import Institution, TechnicalCareer
inst, _ = Institution.objects.get_or_create(name='Universidad Demo')
career, _ = TechnicalCareer.objects.get_or_create(institution=inst, name='Ingenieria')

# Companies and supervisor
from companies.models import Company, Supervisor
comp, _ = Company.objects.get_or_create(
    name='Empresa Demo',
    defaults={'email': 'contact@demo.com', 'is_validated': True}
)

sup_user, sup_user_created = User.objects.get_or_create(
    username='supervisor',
    defaults={'email': 'supervisor@demo.com', 'role': 'COMPANY_SUPERVISOR'}
)
if sup_user_created:
    sup_user.set_password('supervisorpass')
    sup_user.save()

sup, _ = Supervisor.objects.get_or_create(
    company=comp,
    full_name='Supervisor Demo',
    defaults={'email': 'sup@demo.com'}
)

# Student and profile
stu_user, stu_created = User.objects.get_or_create(
    username='student',
    defaults={'email': 'student@demo.com', 'role': 'STUDENT'}
)
if stu_created:
    stu_user.set_password('studentpass')
    stu_user.save()

from internships.models import StudentProfile, Opportunity, Application, Internship, Activity, Evaluation, Evidence

student_profile, _ = StudentProfile.objects.get_or_create(
    user=stu_user,
    defaults={'institution': inst, 'career': career, 'student_code': 'S123', 'is_eligible': True}
)

# Create multiple opportunities
opp_deadline = timezone.now() + timezone.timedelta(days=90)
opportunities = []
for i in range(1, 6):
    opp, _ = Opportunity.objects.get_or_create(
        title=f'Pasantía Demo {i}',
        defaults={
            'institution': inst,
            'company': comp,
            'career': career,
            'description': f'Demo {i}',
            'requirements': [],
            'vacancies': 1,
            'modality': 'REMOTE',
            'deadline': opp_deadline,
            'status': 'ACTIVE',
        }
    )
    opportunities.append(opp)

# Create several applications for the student (to different opportunities)
apps = []
for opp in opportunities[:3]:
    app, _ = Application.objects.get_or_create(
        opportunity=opp,
        student=student_profile,
        defaults={'message': 'Interesado en la oportunidad'}
    )
    apps.append(app)

# For the first application, create an internship in progress
if apps:
    app0 = apps[0]
    intern, _ = Internship.objects.get_or_create(
        application=app0,
        defaults={
            'student': student_profile,
            'company': comp,
            'supervisor': sup,
            'status': 'IN_PROGRESS',
            'start_date': timezone.datetime(2026, 1, 1).date(),
            'end_date': timezone.datetime(2026, 12, 31).date(),
            'total_hours': 16,
        }
    )

    # Create activities
    for j in range(1, 4):
        Activity.objects.get_or_create(
            internship=intern,
            description=f'Actividad demo {j}',
            defaults={'date': (timezone.now() - timezone.timedelta(days=j)).date(), 'hours': 4, 'created_by': admin}
        )

    # Evaluation
    Evaluation.objects.get_or_create(
        internship=intern,
        defaults={'score': 4.5, 'criteria': {'cumplimiento': 4.5}, 'comments': 'Buen trabajo', 'result': 'APPROVED', 'evaluated_by': admin}
    )

    # Evidence
    Evidence.objects.get_or_create(
        internship=intern,
        defaults={'uploaded_by': admin, 'description': 'Evidencia demo 1'}
    )

print('Seeding finished: admin/adminpass, student/studentpass, supervisor/supervisorpass')
