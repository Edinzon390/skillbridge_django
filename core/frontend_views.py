from django.shortcuts import render as django_render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q

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
    # Build context for server-rendered dashboard using same models as API
    user = request.user
    profile = getattr(user, 'student_profile', None)
    context = {}

    from internships.models import Opportunity, Application, Internship, Activity

    # counts and lists
    opportunities_qs = Opportunity.objects.filter(status=Opportunity.Status.ACTIVE)
    context['opportunities_count'] = opportunities_qs.count()

    if profile:
        apps_qs = Application.objects.filter(student=profile)
        context['applications_count'] = apps_qs.count()
        context['pending_applications'] = apps_qs.filter(status=Application.Status.SENT).count()
        context['accepted_count'] = apps_qs.filter(status=Application.Status.ACCEPTED).count()
        internships_qs = Internship.objects.filter(student=profile)
        context['active_internships'] = internships_qs.filter(status=Internship.Status.IN_PROGRESS).count()
        context['recent_applications'] = apps_qs.order_by('-created_at')[:5]
        context['featured_opportunities'] = opportunities_qs.filter(career=profile.career)[:5]
        # active internship object for detailed panel
        context['active_internship'] = internships_qs.filter(status=Internship.Status.IN_PROGRESS).select_related('company', 'supervisor', 'application__opportunity').first()
    else:
        context['applications_count'] = 0
        context['pending_applications'] = 0
        context['accepted_count'] = 0
        context['active_internships'] = 0
        context['recent_applications'] = []
        context['featured_opportunities'] = opportunities_qs[:5]
        context['active_internship'] = None

    return render(request, 'student/dashboard.html', context)


@login_required(login_url='frontend:login')
def internships_list(request):
    return render(request, 'student/opportunities.html')


@login_required(login_url='frontend:login')
def my_applications(request):
    return render(request, 'student/my_applications.html')


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
    user = request.user
    profile = getattr(user, 'student_profile', None)

    if request.method == 'POST':
        # handle simple profile update via session-authenticated form
        student_code = request.POST.get('student_code', '').strip()
        phone = request.POST.get('phone', '').strip()
        bio = request.POST.get('bio', '').strip()
        skills_raw = request.POST.get('skills', '').strip()
        skills = [s.strip() for s in skills_raw.split(',')] if skills_raw else []

        cv = request.FILES.get('cv')
        portfolio = request.FILES.get('portfolio')

        if not profile:
            profile = StudentProfile(user=user)

        if student_code:
            profile.student_code = student_code
        profile.phone = phone
        profile.bio = bio
        if skills:
            profile.skills = skills

        if cv:
            profile.cv = cv
        if portfolio:
            profile.portfolio = portfolio

        profile.save()
        from django.contrib import messages
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('frontend:student-profile')

    return render(request, 'student/profile.html', {'profile': profile})


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
