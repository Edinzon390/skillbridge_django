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
    return render(request, 'student/dashboard.html')


@login_required(login_url='frontend:login')
def internships_list(request):
    return render(request, 'student/opportunities.html')


@login_required(login_url='frontend:login')
def my_applications(request):
    return render(request, 'student/my_applications.html')


@login_required(login_url='frontend:login')
def my_internships(request):
    return render(request, 'student/my_internships.html')


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
    return render(request, 'student/profile.html')


@login_required(login_url='frontend:login')
def company_dashboard(request):
    return render(request, 'company/dashboard.html')


@login_required(login_url='frontend:login')
def company_offers(request):
    from internships.models import Opportunity
    company = getattr(request.user, 'company', None)
    offers = Opportunity.objects.filter(company=company) if company else []
    return render(request, 'company/offers.html', {'offers': offers})


@login_required(login_url='frontend:login')
def applicants_view(request, offer_id):
    return render(request, 'company/applicants.html')


@login_required(login_url='frontend:login')
def company_internships(request, internship_id=None):
    return render(request, 'company/internships.html')


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
