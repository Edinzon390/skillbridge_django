from django.shortcuts import render as django_render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.db import models
from django.utils import timezone

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


@login_required(login_url='frontend:login')
def student_dashboard_json(request):
    """Return aggregate dashboard statistics for the logged-in student."""
    from internships.models import Application, Internship, Opportunity

    student_profile = getattr(request.user, 'student_profile', None)
    if not student_profile:
        return JsonResponse({
            'ok': True,
            'totalApplications': 0,
            'pendingApplications': 0,
            'acceptedApplications': 0,
            'activeInternship': None,
            'availableOpportunities': 0,
            'profileComplete': False,
        })

    total_applications = Application.objects.filter(student=student_profile).count()
    pending_applications = Application.objects.filter(
        student=student_profile, status__in=[Application.Status.SENT, Application.Status.REVIEW]
    ).count()
    accepted_applications = Application.objects.filter(
        student=student_profile, status=Application.Status.ACCEPTED
    ).count()

    active_internship_obj = Internship.objects.filter(
        student=student_profile, status=Internship.Status.IN_PROGRESS
    ).select_related('company').first()

    active_internship = None
    if active_internship_obj:
        active_internship = {
            'id': active_internship_obj.id,
            'company': active_internship_obj.company.name,
            'status': active_internship_obj.get_status_display(),
            'totalHours': active_internship_obj.total_hours,
        }

    available_opportunities = Opportunity.objects.filter(
        status=Opportunity.Status.ACTIVE,
        deadline__gte=timezone.now(),
    ).count()

    return JsonResponse({
        'ok': True,
        'totalApplications': total_applications,
        'pendingApplications': pending_applications,
        'acceptedApplications': accepted_applications,
        'activeInternship': active_internship,
        'availableOpportunities': available_opportunities,
        'profileComplete': bool(student_profile.institution_id and student_profile.career_id),
    })

@login_required(login_url='frontend:login')
def internships_list(request):
    from internships.models import Opportunity, Application

    student_profile = getattr(request.user, 'student_profile', None)

    opportunities = Opportunity.objects.filter(
        status=Opportunity.Status.ACTIVE,
        deadline__gte=timezone.now(),
    ).select_related('company', 'career', 'institution').order_by('-created_at')

    applied_ids = set()
    if student_profile:
        # Priorizar ofertas de la misma carrera del estudiante
        opportunities = opportunities.order_by(
            models.Case(
                models.When(career_id=student_profile.career_id, then=0),
                default=1,
            ),
            '-created_at'
        )
        applied_ids = set(
            Application.objects.filter(student=student_profile).values_list('opportunity_id', flat=True)
        )

    context = {
        'opportunities': opportunities,
        'applied_ids': applied_ids,
        'has_profile': student_profile is not None,
    }
    return render(request, 'student/opportunities.html', context)


@login_required(login_url='frontend:login')
def apply_to_opportunity(request, opportunity_id):
    from django.core.exceptions import ValidationError
    from internships.models import Opportunity, Application

    if request.method != 'POST':
        return redirect('frontend:student-opportunities')

    student_profile = getattr(request.user, 'student_profile', None)
    if student_profile is None:
        messages.error(request, 'Debes completar tu perfil de estudiante antes de aplicar.')
        return redirect('frontend:student-profile')

    opportunity = Opportunity.objects.filter(id=opportunity_id).first()
    if opportunity is None:
        messages.error(request, 'La oportunidad no existe.')
        return redirect('frontend:student-opportunities')

    if Application.objects.filter(opportunity=opportunity, student=student_profile).exists():
        messages.warning(request, f'Ya habías aplicado a "{opportunity.title}".')
        return redirect('frontend:student-opportunities')

    application = Application(
        opportunity=opportunity,
        student=student_profile,
        message=request.POST.get('message', '').strip(),
    )

    try:
        application.full_clean()
        application.save()
        messages.success(request, f'Tu postulación a "{opportunity.title}" fue enviada correctamente.')
    except ValidationError as e:
        for field, errs in e.message_dict.items() if hasattr(e, 'message_dict') else [(None, e.messages)]:
            for msg in errs:
                messages.error(request, msg)

    return redirect('frontend:student-opportunities')


@login_required(login_url='frontend:login')
def my_applications(request):
    from internships.models import Application

    student_profile = getattr(request.user, 'student_profile', None)
    applications_qs = []
    if student_profile:
        applications_qs = Application.objects.filter(
            student=student_profile
        ).select_related('opportunity', 'opportunity__company').order_by('-created_at')

    status_class_map = {
        'SENT': 'pending',
        'REVIEW': 'pending',
        'ACCEPTED': 'success',
        'REJECTED': 'danger',
    }

    applications = []
    review_count = 0
    accepted_count = 0
    for app in applications_qs:
        applications.append({
            'company': app.opportunity.company.name,
            'position': app.opportunity.title,
            'status': app.get_status_display(),
            'status_class': status_class_map.get(app.status, 'pending'),
            'location': app.opportunity.get_modality_display(),
            'applied_at': app.created_at,
            'updated_at': app.created_at,
            'deadline': app.opportunity.deadline,
            'description': app.opportunity.description,
        })
        if app.status == 'REVIEW' or app.status == 'SENT':
            review_count += 1
        if app.status == 'ACCEPTED':
            accepted_count += 1

    context = {
        'applications': applications,
        'total_applications': len(applications),
        'review_count': review_count,
        'accepted_count': accepted_count,
    }
    return render(request, 'student/my_applications.html', context)


@login_required(login_url='frontend:login')
def my_internships(request):
    from internships.models import Internship
    internships = []
    try:
        student_profile = getattr(request.user, 'student_profile', None)
        if student_profile:
            internships = Internship.objects.filter(student=student_profile).select_related('company', 'supervisor', 'application')
    except Exception:
        internships = []
    return render(request, 'student/my_internships.html', {'internships': internships})


@login_required(login_url='frontend:login')
def view_internship(request, internship_id):
    from internships.models import Opportunity
    internship = Opportunity.objects.filter(id=internship_id).first()
    return render(request, 'student/internship_detail.html', {'internship': internship})


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
    applications = opp.applications.select_related('student__user').all()
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


@login_required(login_url='frontend:login')
def careers_by_institution_json(request, institution_id):
    from institutions.models import TechnicalCareer
    careers = TechnicalCareer.objects.filter(
        institution_id=institution_id, is_active=True
    ).order_by('name')
    return JsonResponse({
        'careers': [{'id': c.id, 'name': c.name} for c in careers]
    })


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