from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from accounts.models import Role, User
from companies.models import Company, Supervisor
from internships.models import Opportunity, Application, Internship
from institutions.models import Institution, TechnicalCareer
from django.utils import timezone

from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json


def get_dashboard_redirect_url(user):
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
        # Create user with provided credentials (corrected)
        user = User.objects.create_user(username=username, email=email, password=password)
        user.role = role
        user.save()

        if role == Role.COMPANY and company_name:
            company, created = Company.objects.get_or_create(name=company_name)
            if created:
                # New companies require admin validation by default; leave is_validated False
                company.is_active = True
                company.save()
            user.company = company
            user.save()

        login(request, user)
        messages.success(request, 'Cuenta creada correctamente.')
        return redirect(get_dashboard_redirect_url(user))

    return render(request, 'auth/register.html')


def register_submit_v2(request):
    """Improved register handler that accepts full_name for students and uses company name for company users."""
    if request.user.is_authenticated:
        return redirect(get_dashboard_redirect_url(request.user))

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()
        selected_role = request.POST.get('role', '').strip().lower()
        company_name = request.POST.get('company_name', '').strip()
        full_name = request.POST.get('full_name', '').strip()

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
        user = User.objects.create_user(username=username, email=email, password=password)
        user.role = role

        if role == Role.COMPANY:
            if company_name:
                company, created = Company.objects.get_or_create(name=company_name)
                if created:
                    company.is_active = True
                    company.save()
                user.company = company
                user.first_name = company.name
        else:
            if full_name:
                parts = full_name.split()
                user.first_name = parts[0]
                user.last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''

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
            # Do not auto-validate companies created during offer creation
            company.save()
            user.company = company
            user.save()

        title = request.POST.get('position', '').strip() or 'Sin título'
        description = request.POST.get('description', '').strip()
        location = request.POST.get('location', '').strip()
        location_type = request.POST.get('location_type', 'on-site')
        area = request.POST.get('area', '').strip()
        required_skills = request.POST.get('required_skills', '')
        nice_to_have = request.POST.get('nice_to_have', '')
        benefits = request.POST.get('benefits', '')
        is_paid = bool(request.POST.get('is_paid'))
        salary_min = request.POST.get('salary_min') or None
        salary_max = request.POST.get('salary_max') or None
        supervisor_name = request.POST.get('supervisor_name', '').strip()
        supervisor_email = request.POST.get('supervisor_email', '').strip()
        supervisor_phone = request.POST.get('supervisor_phone', '').strip()
        contact_email = request.POST.get('contact_email', '').strip()
        contact_phone = request.POST.get('contact_phone', '').strip()
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


@login_required(login_url='frontend:login')
def edit_offer_view(request, offer_id):
    # Prefer a safe lookup so we can show a friendly message instead of a hard 404
    opp = Opportunity.objects.filter(id=offer_id).first()
    if not opp:
        messages.error(request, 'La oferta solicitada no existe.')
        return redirect('frontend:company-offers')

    user = request.user
    if not (user.is_staff or user.is_superuser or (hasattr(user, 'company') and user.company and user.company.id == opp.company_id)):
        messages.error(request, 'No tienes permisos para editar esta oferta.')
        return redirect('frontend:company-offers')

    if request.method == 'POST':
        opp.title = request.POST.get('position', opp.title).strip()
        opp.description = request.POST.get('description', opp.description).strip()
        area = request.POST.get('area', '')
        career, _ = TechnicalCareer.objects.get_or_create(institution=opp.institution, name=area or 'General')
        opp.career = career
        opp.requirements = [s.strip() for s in request.POST.get('required_skills', '').split(',') if s.strip()]
        # Keep vacancies if not provided; fall back to current value
        try:
            opp.vacancies = int(request.POST.get('vacancies') or opp.vacancies)
        except Exception:
            pass
        loc_type = request.POST.get('location_type', 'on-site')
        modality_map = {'on-site': Opportunity.Modality.PRESENTIAL, 'remote': Opportunity.Modality.REMOTE, 'hybrid': Opportunity.Modality.HYBRID}
        opp.modality = modality_map.get(loc_type, opp.modality)
        deadline = request.POST.get('deadline')
        if deadline:
            try:
                d = timezone.datetime.strptime(deadline, '%Y-%m-%d').date()
                opp.deadline = timezone.make_aware(timezone.datetime(d.year, d.month, d.day, 23, 59, 59))
            except Exception:
                pass
        opp.save()

        supervisor_email = request.POST.get('supervisor_email', '').strip()
        if supervisor_email:
            supervisor_name = request.POST.get('supervisor_name', '').strip()
            supervisor_phone = request.POST.get('supervisor_phone', '').strip()
            Supervisor.objects.update_or_create(
                company=opp.company,
                email=supervisor_email,
                defaults={'full_name': supervisor_name or supervisor_email.split('@')[0], 'phone': supervisor_phone}
            )

        messages.success(request, 'Oferta actualizada correctamente.')
        return redirect('frontend:company-offers')

    context = {'offer': opp}
    return render(request, 'company/create-offer.html', context)


@login_required(login_url='frontend:login')
def company_profile_view(request):
    user = request.user
    company = getattr(user, 'company', None)
    if not company:
        messages.info(request, 'No tienes una empresa asociada. Puedes crear una en el registro o en el perfil.')
        return redirect('frontend:company-dashboard')

    if request.method == 'POST':
        company.name = request.POST.get('name', company.name).strip()
        company.email = request.POST.get('email', company.email).strip()
        company.phone = request.POST.get('phone', company.phone).strip()
        company.website = request.POST.get('website', company.website).strip()
        company.address = request.POST.get('address', company.address).strip()
        company.save()
        messages.success(request, 'Perfil de empresa actualizado.')
        return redirect('frontend:company-profile')

    return render(request, 'company/profile.html', {'company': company})


@require_POST
def save_chat_message(request):
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    except Exception:
        data = request.POST

    user_message = data.get('user_message') or data.get('user_message', '')
    bot_response = data.get('bot_response') or data.get('bot_response', '')

    user = request.user if request.user.is_authenticated else None
    try:
        from notifications.models import SupportMessage
        SupportMessage.objects.create(user=user, user_message=user_message, bot_response=bot_response)
    except Exception:
        return JsonResponse({'ok': False}, status=500)

    return JsonResponse({'ok': True})


@login_required(login_url='frontend:login')
def company_offers_json(request):
    """Return a JSON list of offers that belong to the logged-in user's company."""
    user = request.user
    company = getattr(user, 'company', None)
    if not company:
        return JsonResponse({'offers': []})

    qs = Opportunity.objects.filter(company=company).order_by('-created_at')
    offers = []
    for opp in qs:
        offers.append({
            'id': opp.id,
            'title': opp.title,
            'description': (opp.description[:200] + '...') if len(opp.description or '') > 200 else (opp.description or ''),
            'modality': opp.get_modality_display() if hasattr(opp, 'get_modality_display') else opp.modality,
            'applicants': opp.applications.count() if hasattr(opp, 'applications') else 0,
            'vacancies': opp.vacancies,
            'status': opp.status,
        })
    return JsonResponse({'offers': offers})


from django.db.models import Avg


@login_required(login_url='frontend:login')
def student_dashboard_json(request):
    """Return the data used by the student dashboard from the real database."""
    student_profile = getattr(request.user, 'student_profile', None)
    if not student_profile:
        return JsonResponse({
            'stats': {
                'opportunities': 0,
                'applications': 0,
                'accepted': 0,
                'active': 0,
                'pending': 0,
            },
            'featuredOpportunities': [],
            'recentApplications': [],
            'milestones': [],
        })

    active_opportunities = Opportunity.objects.filter(
        status=Opportunity.Status.ACTIVE,
        deadline__gte=timezone.now(),
    ).select_related('company').order_by('-created_at')[:6]

    student_applications_all = Application.objects.filter(student=student_profile).select_related('opportunity__company').order_by('-created_at')
    student_applications = student_applications_all[:10]
    active_internships = Internship.objects.filter(student=student_profile, status=Internship.Status.IN_PROGRESS).select_related('application__opportunity', 'company').order_by('-created_at')

    stats = {
        'opportunities': active_opportunities.count(),
        'applications': student_applications_all.count(),
        'accepted': student_applications_all.filter(status=Application.Status.ACCEPTED).count(),
        'active': active_internships.count(),
        'pending': student_applications_all.filter(status__in=[Application.Status.SENT, Application.Status.REVIEW]).count(),
    }

    featured_opportunities = []
    for opp in active_opportunities[:3]:
        featured_opportunities.append({
            'id': opp.id,
            'title': opp.title,
            'company': opp.company.name if opp.company else 'Empresa',
            'hours': opp.vacancies if opp.vacancies else 0,
            'deadline': opp.deadline.isoformat() if opp.deadline else None,
            'url': f"/student/opportunities/{opp.id}/",
        })

    recent_applications = []
    for app in student_applications[:3]:
        status = app.status
        status_map = {
            Application.Status.SENT: ('pending', 'Pendiente'),
            Application.Status.REVIEW: ('pending', 'En revisión'),
            Application.Status.ACCEPTED: ('accepted', 'Aceptada'),
            Application.Status.REJECTED: ('rejected', 'Rechazada'),
        }
        status_class, status_label = status_map.get(status, ('pending', 'Pendiente'))
        recent_applications.append({
            'id': app.id,
            'position': app.opportunity.title if app.opportunity else 'Sin posición',
            'company': app.opportunity.company.name if app.opportunity and app.opportunity.company else 'Empresa',
            'status': status_class,
            'statusLabel': status_label,
            'date': app.created_at.date().isoformat() if app.created_at else None,
        })

    milestones = []
    for opp in active_opportunities[:4]:
        milestones.append({
            'event': f'Aplicación abierta - {opp.title}',
            'date': opp.deadline.date().isoformat() if opp.deadline else timezone.now().date().isoformat(),
            'status': 'Por venir',
        })

    for internship in active_internships[:2]:
        if internship.end_date:
            milestones.append({
                'event': f'Fin de pasantía - {internship.application.opportunity.title if internship.application and internship.application.opportunity else "Pasantía"}',
                'date': internship.end_date.isoformat(),
                'status': 'Activo',
            })

    return JsonResponse({
        'stats': stats,
        'featuredOpportunities': featured_opportunities,
        'recentApplications': recent_applications,
        'milestones': milestones[:4],
    })

@login_required(login_url='frontend:login')
def company_dashboard_json(request):
    """Return aggregate dashboard statistics for the logged-in company."""
    user = request.user
    company = getattr(user, 'company', None)
    if not company:
        return JsonResponse({'ok': True, 'activeOffers': 0, 'totalApplicants': 0, 'pendingReview': 0, 'activeInternships': 0, 'avgRating': 0})

    active_offers = Opportunity.objects.filter(company=company, status=Opportunity.Status.ACTIVE).count()
    total_applicants = Application.objects.filter(opportunity__company=company).count()
    pending_review = Application.objects.filter(opportunity__company=company, status__in=[Application.Status.SENT, Application.Status.REVIEW]).count()
    active_internships = Internship.objects.filter(company=company, status=Internship.Status.IN_PROGRESS).count()

    # Acceptance metrics: accepted applications / total applications
    accepted_applications = Application.objects.filter(opportunity__company=company, status=Application.Status.ACCEPTED).count()
    total_applications = total_applicants
    acceptance_rate = 0
    if total_applications:
        try:
            acceptance_rate = round((accepted_applications / total_applications) * 100)
        except Exception:
            acceptance_rate = 0

    # Average rating (if evaluations app exists)
    avg_rating = None
    try:
        from evaluations.models import Evaluation as EvalModel
        agg = EvalModel.objects.filter(internship__company=company).aggregate(avg=Avg('score'))
        avg_rating = agg.get('avg') or 0
    except Exception:
        avg_rating = 0

    # Normalize float to one decimal
    try:
        avg_rating = round(float(avg_rating), 1)
    except Exception:
        avg_rating = 0

    return JsonResponse({
        'ok': True,
        'activeOffers': active_offers,
        'totalApplicants': total_applicants,
        'pendingReview': pending_review,
        'activeInternships': active_internships,
        'acceptedApplications': accepted_applications,
        'totalApplications': total_applications,
        'acceptanceRate': acceptance_rate,
        'avgRating': avg_rating,
    })


@login_required(login_url='frontend:login')
def company_internships_json(request):
    """Return active internships (in progress) for the logged-in company as JSON."""
    user = request.user
    company = getattr(user, 'company', None)
    if not company:
        return JsonResponse({'internships': []})

    qs = Internship.objects.filter(company=company, status=Internship.Status.IN_PROGRESS).select_related('student__user', 'application__opportunity')
    items = []
    for it in qs:
        student_name = it.student.user.get_full_name() or it.student.user.username
        opp_title = ''
        try:
            opp_title = it.application.opportunity.title
        except Exception:
            opp_title = ''
        items.append({
            'id': it.id,
            'student': student_name,
            'position': opp_title,
            'start': it.start_date.isoformat() if it.start_date else None,
            'end': it.end_date.isoformat() if it.end_date else None,
            'hours': f"{it.total_hours}",
        })
    return JsonResponse({'internships': items})


@login_required(login_url='frontend:login')
def company_pending_applicants_json(request):
    """Return pending applicants (applications with SENT or REVIEW) for the logged-in company's offers."""
    user = request.user
    company = getattr(user, 'company', None)
    if not company:
        return JsonResponse({'applications': []})

    qs = Application.objects.filter(opportunity__company=company, status__in=[Application.Status.SENT, Application.Status.REVIEW]).select_related('student__user', 'opportunity').order_by('-created_at')[:20]
    applications = []
    for app in qs:
        student_name = app.student.user.get_full_name() or app.student.user.username
        applications.append({
            'id': app.id,
            'name': student_name,
            'position': app.opportunity.title if app.opportunity else '',
            'date': app.created_at.date().isoformat(),
            'rating': None,
        })

    return JsonResponse({'applications': applications})


@login_required(login_url='frontend:login')
@require_POST
def delete_offer_view(request, offer_id):
    """Mark an opportunity as CANCELLED instead of removing it from the database.

    Only the owning company (or staff/superuser) may perform this action.
    """
    opp = Opportunity.objects.filter(id=offer_id).first()
    if not opp:
        messages.error(request, 'La oferta solicitada no existe.')
        return redirect('frontend:company-offers')

    user = request.user
    if not (user.is_staff or user.is_superuser or (hasattr(user, 'company') and user.company and user.company.id == opp.company_id)):
        messages.error(request, 'No tienes permisos para cancelar esta oferta.')
        return redirect('frontend:company-offers')

    if opp.status == Opportunity.Status.CANCELLED:
        messages.info(request, 'La oferta ya está cancelada.')
        return redirect('frontend:company-offers')

    # Mark as cancelled to preserve history
    opp.status = Opportunity.Status.CANCELLED
    opp.save()
    messages.success(request, 'Oferta marcada como cancelada.')
    return redirect('frontend:company-offers')
