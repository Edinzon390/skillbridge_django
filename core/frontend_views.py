from django.shortcuts import render as django_render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from datetime import timedelta

from .frontend_actions_clean import get_dashboard_redirect_url, register_submit, create_offer_view, edit_offer_view, company_profile_view, save_chat_message


def render(request, template_name, context=None, *args, **kwargs):
    context = dict(context or {})
    return django_render(request, template_name, context, *args, **kwargs)


def home(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_redirect_url(request.user))
    return render(request, 'home.html')


def help_page(request):
    return render(request, 'help.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_redirect_url(request.user))

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if username_or_email and password:
            from accounts.models import User
            user_obj = User.objects.filter(Q(username=username_or_email) | Q(email=username_or_email)).first()
            if user_obj is not None:
                user = authenticate(request, username=user_obj.username, password=password)
            else:
                user = authenticate(request, username=username_or_email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, 'Login correcto.')
                return redirect(get_dashboard_redirect_url(user))

        messages.error(request, 'Credenciales invalidas. Intenta con las credenciales de prueba.')

    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'Sesion cerrada.')
    return redirect('frontend:login')


def password_reset_view(request):
    if request.method == 'POST':
        messages.info(request, 'Si el correo existe, recibiras instrucciones para recuperar tu contrasena.')
    return render(request, 'auth/password-reset.html')


@login_required(login_url='frontend:login')
def student_dashboard(request):
    return render(request, 'student/dashboard.html')


def _opportunity_area_key(area_name):
    normalized = (area_name or '').strip().lower()
    if 'front' in normalized:
        return 'frontend'
    if 'back' in normalized:
        return 'backend'
    if 'full' in normalized or 'stack' in normalized:
        return 'fullstack'
    if 'devops' in normalized or 'ops' in normalized:
        return 'devops'
    if 'qa' in normalized or 'quality' in normalized:
        return 'qa'
    if 'data' in normalized or 'science' in normalized:
        return 'datascience'
    return 'backend'


def _serialize_opportunity_for_frontend(opportunity):
    company = opportunity.company
    career = opportunity.career
    institution = opportunity.institution
    institution_config = getattr(institution, 'config', None)

    location_name = 'Bogotá'
    location_key = 'bogota'
    modality_text = (opportunity.modality or '').lower()
    if 'remote' in modality_text:
        location_name = 'Remoto'
        location_key = 'remoto'
    else:
        address = (company.address or '').lower()
        if 'medell' in address:
            location_name = 'Medellín'
            location_key = 'medellin'
        elif 'cali' in address:
            location_name = 'Cali'
            location_key = 'cali'
        elif 'barranquilla' in address:
            location_name = 'Barranquilla'
            location_key = 'barranquilla'

    area_name = career.name if career else 'General'
    area_key = _opportunity_area_key(area_name)
    required_hours = getattr(institution_config, 'required_hours', None) or 160

    return {
        'id': str(opportunity.id),
        'position': opportunity.title,
        'company': company.name,
        'company_description': company.website or company.address or company.name,
        'location': location_name,
        'location_key': location_key,
        'area': area_name,
        'area_key': area_key,
        'required_hours': int(required_hours),
        'deadline': opportunity.deadline.isoformat() if opportunity.deadline else (opportunity.created_at + timedelta(days=30)).isoformat(),
        'description': opportunity.description or 'Sin descripción disponible.',
        'required_skills': list(opportunity.requirements or []),
        'applicants_count': opportunity.applications.count(),
        'created_at': opportunity.created_at.isoformat(),
    }


@login_required(login_url='frontend:login')
def internships_list(request):
    from internships.models import Opportunity

    opportunities = (
        Opportunity.objects.filter(status=Opportunity.Status.ACTIVE)
        .select_related('company', 'institution', 'career')
        .prefetch_related('applications')
        .order_by('-created_at')
    )
    opportunities_data = [_serialize_opportunity_for_frontend(item) for item in opportunities]
    return render(request, 'student/opportunities.html', {'opportunities_json': opportunities_data})


@login_required(login_url='frontend:login')
def opportunity_detail_json(request, opportunity_id):
    from internships.models import Opportunity

    opportunity = get_object_or_404(
        Opportunity.objects.select_related('company', 'institution', 'career'),
        id=opportunity_id,
        status=Opportunity.Status.ACTIVE,
    )
    data = _serialize_opportunity_for_frontend(opportunity)
    data['company'] = {
        'name': data['company'],
        'description': data['company_description'],
    }
    return JsonResponse(data)


@login_required(login_url='frontend:login')
def my_applications(request):
    from internships.models import Application

    applications = (
        Application.objects.filter(student__user=request.user)
        .select_related('opportunity__company', 'opportunity')
        .order_by('-created_at')
    )
    status_labels = {
        Application.Status.SENT: ('Enviada', 'pending'),
        Application.Status.REVIEW: ('En revisión', 'review'),
        Application.Status.ACCEPTED: ('Aceptada', 'accepted'),
        Application.Status.REJECTED: ('Rechazada', 'rejected'),
    }
    application_rows = []
    for application in applications:
        status_label, status_class = status_labels.get(
            application.status,
            (application.get_status_display(), 'pending'),
        )
        opportunity = application.opportunity
        application_rows.append({
            'id': application.id,
            'opportunity_id': opportunity.id,
            'company': opportunity.company.name,
            'position': opportunity.title,
            'status': status_label,
            'status_class': status_class,
            'location': opportunity.get_modality_display(),
            'applied_at': application.created_at.strftime('%d/%m/%Y'),
            'deadline': opportunity.deadline.strftime('%d/%m/%Y') if opportunity.deadline else '',
            'description': opportunity.description,
            'updated_at': application.created_at.strftime('%d/%m/%Y'),
        })

    return render(request, 'student/my_applications.html', {
        'applications': application_rows,
        'total_applications': len(application_rows),
        'review_count': sum(item['status_class'] == 'review' for item in application_rows),
        'accepted_count': sum(item['status_class'] == 'accepted' for item in application_rows),
    })


@login_required(login_url='frontend:login')
def apply_to_opportunity(request, opportunity_id):
    from internships.models import Application, Opportunity, StudentProfile
    from institutions.models import Institution, TechnicalCareer

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Solo se permite aplicar mediante POST.'}, status=405)

    opportunity = get_object_or_404(
        Opportunity,
        id=opportunity_id,
        status=Opportunity.Status.ACTIVE,
    )
    profile = StudentProfile.objects.filter(user=request.user).first()
    if profile is None:
        institution, _ = Institution.objects.get_or_create(name='Plataforma Pública')
        career, _ = TechnicalCareer.objects.get_or_create(
            institution=institution,
            name='General',
        )
        profile = StudentProfile.objects.create(
            user=request.user,
            institution=institution,
            career=career,
            student_code=f'AUTO-{request.user.id}',
            is_eligible=True,
        )
    elif not profile.is_eligible:
        return JsonResponse({
            'ok': False,
            'error': 'Tu perfil aún no está habilitado para postularse.',
        }, status=400)

    application, created = Application.objects.get_or_create(
        opportunity=opportunity,
        student=profile,
        defaults={'message': request.POST.get('message', '').strip()},
    )
    if not created:
        return JsonResponse({
            'ok': False,
            'already_applied': True,
            'error': 'Ya te postulaste a esta oportunidad.',
        }, status=409)

    return JsonResponse({
        'ok': True,
        'application_id': application.id,
        'message': 'Postulación enviada correctamente.',
    }, status=201)


@login_required(login_url='frontend:login')
def my_internships(request):
    from internships.models import Internship
    internships = []
    try:
        student_profile = getattr(request.user, 'student_profile', None)
        if student_profile:
            internships = Internship.objects.filter(student=student_profile).select_related(
                'company', 'supervisor', 'application__opportunity'
            )
    except Exception:
        internships = []
    return render(request, 'student/my_internships.html', {'internships': internships})


@login_required(login_url='frontend:login')
def view_internship(request, internship_id):
    from internships.models import Opportunity
    opportunity = get_object_or_404(
        Opportunity.objects.select_related('company', 'institution', 'career'),
        id=internship_id,
    )
    return render(request, 'student/opportunity_detail.html', {'opportunity': opportunity})


@login_required(login_url='frontend:login')
def log_hours(request, internship_id):
    """Lightweight endpoint for logging hours from the frontend.
    Accepts POST requests with hours data and returns JSON OK; otherwise redirects back to dashboard."""
    if request.method == 'POST':
        # Placeholder: real implementation should validate and create HoursLog model entries
        return JsonResponse({'ok': True})
    return redirect('frontend:student-dashboard')


@login_required(login_url='frontend:login')
def student_profile(request):
    return render(request, 'student/profile.html')


@login_required(login_url='frontend:login')
def company_dashboard(request):
    return render(request, 'company/dashboard.html')


@login_required(login_url='frontend:login')
def company_internships(request, internship_id=None):
    # Show internships for the logged-in company user
    from internships.models import Internship
    company = getattr(request.user, 'company', None)
    internships = []
    if company:
        internships = Internship.objects.filter(company=company).select_related('student__user', 'supervisor', 'application__opportunity')
    context = {'internships': internships}
    return render(request, 'company/internships.html', context)


@login_required(login_url='frontend:login')
def company_offers(request):
    from internships.models import Opportunity
    company = getattr(request.user, 'company', None)
    offers = Opportunity.objects.filter(company=company) if company else []
    return render(request, 'company/offers.html', {'offers': offers})


@login_required(login_url='frontend:login')
def applicants_view(request, offer_id):
    from internships.models import Opportunity, Application
    opp = Opportunity.objects.filter(id=offer_id).first()
    if not opp:
        messages.error(request, 'La oferta solicitada no existe.')
        return redirect('frontend:company-offers')

    user = request.user
    if not (user.is_staff or user.is_superuser or (hasattr(user, 'company') and user.company and user.company.id == opp.company_id)):
        messages.error(request, 'No tienes permisos para ver los aplicantes de esta oferta.')
        return redirect('frontend:company-offers')

    # Only return real applications stored in DB
    applications = opp.applications.select_related(
        'student__user',
        'student__institution',
        'student__career',
    ).all()
    return render(request, 'company/applicants.html', {'applications': applications, 'offer': opp})




@login_required(login_url='frontend:login')
def hours_validation(request):
    return render(request, 'company/hours_validation.html')


@login_required(login_url='frontend:login')
def admin_dashboard(request):
    return render(request, 'admin/dashboard.html')


@login_required(login_url='frontend:login')
def students_management(request):
    return render(request, 'admin/students.html')


@login_required(login_url='frontend:login')
def companies_management(request):
    return render(request, 'admin/companies.html')


@login_required(login_url='frontend:login')
def internships_monitoring(request):
    return render(request, 'admin/internships.html')


@login_required(login_url='frontend:login')
def institutions_view(request):
    return render(request, 'admin/institutions.html')


@login_required(login_url='frontend:login')
def users_management(request):
    return render(request, 'admin/users.html')


@login_required(login_url='frontend:login')
def export_report(request):
    return JsonResponse({'ok': True})


def user_roles(request):
    """Context processor: inject user's roles into template context as 'user_roles'."""
    roles = []
    if getattr(request, 'user', None) and request.user.is_authenticated:
        role = getattr(request.user, 'role', None)
        if role:
            roles = [role]
    return {'user_roles': roles}


def get_user_roles(request):
    """API endpoint that returns the current user's roles as JSON."""
    roles = []
    if getattr(request, 'user', None) and request.user.is_authenticated:
        role = getattr(request.user, 'role', None)
        if role:
            roles = [role]
    return JsonResponse({'roles': roles})

@login_required(login_url='frontend:login')
def student_profile(request):
    from internships.models import StudentProfile
    from institutions.models import Institution, TechnicalCareer

    if request.user.role != 'STUDENT':
        messages.error(request, 'Esta sección es solo para estudiantes.')
        return redirect(get_dashboard_redirect_url(request.user))

    profile = getattr(request.user, 'student_profile', None)
    institutions = Institution.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        institution_id = request.POST.get('institution')
        career_id = request.POST.get('career')
        student_code = request.POST.get('student_code', '').strip()
        phone = request.POST.get('phone', '').strip()
        bio = request.POST.get('bio', '').strip()
        skills_raw = request.POST.get('skills', '')
        skills = [s.strip() for s in skills_raw.split(',') if s.strip()]

        errors = []
        institution = Institution.objects.filter(id=institution_id).first() if institution_id else None
        career = TechnicalCareer.objects.filter(id=career_id, institution=institution).first() if (career_id and institution) else None

        if not institution:
            errors.append('Selecciona una institución válida.')
        if not career:
            errors.append('Selecciona una carrera técnica válida.')
        if not student_code:
            errors.append('El código de estudiante es obligatorio.')
        elif StudentProfile.objects.filter(student_code=student_code).exclude(
            user=request.user
        ).exists():
            errors.append('Ese código de estudiante ya está en uso.')

        if not errors:
            if profile is None:
                profile = StudentProfile(user=request.user)
            profile.institution = institution
            profile.career = career
            profile.student_code = student_code
            profile.phone = phone
            profile.bio = bio
            profile.skills = skills

            if request.FILES.get('cv'):
                profile.cv = request.FILES['cv']
            if request.FILES.get('portfolio'):
                profile.portfolio = request.FILES['portfolio']

            profile.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('frontend:student-profile')

        for error in errors:
            messages.error(request, error)

    careers = []
    if profile and profile.institution_id:
        careers = TechnicalCareer.objects.filter(institution=profile.institution, is_active=True)
    elif institutions:
        careers = TechnicalCareer.objects.filter(institution=institutions.first(), is_active=True) if institutions.exists() else []

    context = {
        'profile': profile,
        'institutions': institutions,
        'careers': careers,
        'skills_text': ', '.join(profile.skills) if profile and profile.skills else '',
    }
    return render(request, 'student/profile.html', context)


@login_required(login_url='frontend:login')
def careers_by_institution_json(request, institution_id):
    from institutions.models import TechnicalCareer
    careers = TechnicalCareer.objects.filter(
        institution_id=institution_id, is_active=True
    ).order_by('name')
    return JsonResponse({
        'careers': [{'id': c.id, 'name': c.name} for c in careers]
    })