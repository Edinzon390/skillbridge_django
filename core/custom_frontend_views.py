from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from accounts.models import Role, User
from companies.models import Company, Supervisor
from internships.models import Opportunity
from institutions.models import Institution, TechnicalCareer
from django.utils import timezone


def get_dashboard_redirect_url(user):
    # Simple redirection helper compatible with existing logic
    if not user.is_authenticated:
        return 'frontend:login'
    if user.role in {Role.COORDINATOR, Role.INSTITUTION_ADMIN, Role.SUPER_ADMIN}:
        return 'frontend:admin-dashboard'
    if user.role == Role.COMPANY:
        return 'frontend:company-dashboard'
    return 'frontend:student-dashboard'


def register_submit(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_redirect_url(request.user))

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()
        selected_role = request.POST.get('role', '').strip().lower()
        company_name = request.POST.get('company_name', '').strip()

        if not email or not password:
            messages.error(request, 'El correo y la contraseña son obligatorios.')
            return render(request, 'auth/register.html')

        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base_username}{counter}'
            counter += 1

        role = Role.COMPANY if selected_role == 'company' else Role.STUDENT
        user = User.objects.create_user(username=username, email=email, password=password, role=role)

        if role == Role.COMPANY and company_name:
            company, created = Company.objects.get_or_create(name=company_name)
            if created:
                company.is_validated = True
                company.is_active = True
                company.save()
            user.company = company
            user.save()

        login(request, user)
        messages.success(request, 'Cuenta creada correctamente.')
        return redirect(get_dashboard_redirect_url(user))

    return render(request, 'auth/register.html')


@login_required(login_url='frontend:login')
def create_offer_view(request):
    if request.method == 'POST':
        user = request.user
        company = getattr(user, 'company', None)
        if company is None:
            company_name = request.POST.get('company_name', '').strip() or f'Empresa de {user.username}'
            company, _ = Company.objects.get_or_create(name=company_name)
            company.is_validated = True
            company.save()
            user.company = company
            user.save()

        title = request.POST.get('position', '').strip() or 'Sin título'
        description = request.POST.get('description', '').strip()
        location_type = request.POST.get('location_type', 'on-site')
        area = request.POST.get('area', '').strip()
        required_skills = request.POST.get('required_skills', '')
        supervisor_name = request.POST.get('supervisor_name', '').strip()
        supervisor_email = request.POST.get('supervisor_email', '').strip()
        supervisor_phone = request.POST.get('supervisor_phone', '').strip()
        deadline = request.POST.get('deadline')

        modality_map = {
            'on-site': Opportunity.Modality.PRESENTIAL,
            'remote': Opportunity.Modality.REMOTE,
            'hybrid': Opportunity.Modality.HYBRID
        }
        modality = modality_map.get(location_type, Opportunity.Modality.PRESENTIAL)

        institution, _ = Institution.objects.get_or_create(name='Plataforma Pública')
        career, _ = TechnicalCareer.objects.get_or_create(institution=institution, name=area or 'General')

        requirements_list = [s.strip() for s in required_skills.split(',') if s.strip()]

        deadline_dt = None
        if deadline:
            try:
                d = timezone.datetime.strptime(deadline, '%Y-%m-%d').date()
                deadline_dt = timezone.make_aware(timezone.datetime(d.year, d.month, d.day, 23, 59, 59))
            except Exception:
                deadline_dt = None

        supervisor = None
        if supervisor_email:
            supervisor, _ = Supervisor.objects.get_or_create(
                company=company,
                email=supervisor_email,
                defaults={'full_name': supervisor_name or supervisor_email.split('@')[0], 'phone': supervisor_phone}
            )

        opp = Opportunity.objects.create(
            institution=institution,
            company=company,
            career=career,
            title=title,
            description=description or 'Sin descripción',
            requirements=requirements_list,
            vacancies=1,
            modality=modality,
            deadline=deadline_dt or timezone.now() + timezone.timedelta(days=30),
            status=Opportunity.Status.ACTIVE
        )

        messages.success(request, 'Oferta creada correctamente.')
        return redirect('frontend:company-offers')

    # GET -> render the create offer template
    return render(request, 'company/create-offer.html')
