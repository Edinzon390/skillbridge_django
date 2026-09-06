from datetime import timedelta
from math import ceil

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from accounts.models import Role, User
from companies.models import Company, Supervisor
from internships.models import Opportunity, Application, Internship
from institutions.models import Institution, TechnicalCareer, InstitutionConfig
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
    if request.user.role != Role.COMPANY:
        messages.error(request, 'Solo las cuentas de empresa pueden publicar ofertas.')
        return redirect(get_dashboard_redirect_url(request.user))

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

        if not title or not description or not deadline:
            messages.error(request, 'Completa el título, la descripción y la fecha límite.')
            return render(request, 'company/create-offer.html')

        try:
            d = timezone.datetime.strptime(deadline, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'La fecha límite no es válida.')
            return render(request, 'company/create-offer.html')
        deadline_dt = timezone.make_aware(timezone.datetime(d.year, d.month, d.day, 23, 59, 59))

        try:
            vacancies = max(1, int(request.POST.get('vacancies') or 1))
        except ValueError:
            messages.error(request, 'La cantidad de vacantes no es válida.')
            return render(request, 'company/create-offer.html')

        try:
            required_hours = max(1, int(request.POST.get('required_hours') or 0))
        except ValueError:
            messages.error(request, 'La cantidad de horas requeridas no es válida.')
            return render(request, 'company/create-offer.html')

        supervisor = None
        if supervisor_email:
            supervisor, _ = Supervisor.objects.get_or_create(
                company=company,
                email=supervisor_email,
                defaults={'full_name': supervisor_name or supervisor_email.split('@')[0], 'phone': supervisor_phone}
            )

        Opportunity.objects.create(
            institution=institution,
            company=company,
            career=career,
            title=title,
            description=description or 'Sin descripción',
            requirements=requirements_list,
            vacancies=vacancies,
            required_hours=required_hours,
            modality=modality,
            deadline=deadline_dt,
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
        try:
            opp.required_hours = max(1, int(request.POST.get('required_hours') or opp.required_hours))
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
    if not company and not (user.is_staff or user.is_superuser):
        return JsonResponse({'offers': []})

    qs = Opportunity.objects.all() if user.is_staff or user.is_superuser else Opportunity.objects.filter(company=company)
    qs = qs.order_by('-created_at')[:4]
    offers = []
    for opp in qs:
        offers.append({
            'id': opp.id,
            'title': opp.title,
            'description': (opp.description[:200] + '...') if len(opp.description or '') > 200 else (opp.description or ''),
            'modality': opp.get_modality_display() if hasattr(opp, 'get_modality_display') else opp.modality,
            'applicants': opp.applications.count() if hasattr(opp, 'applications') else 0,
            'vacancies': opp.vacancies,
            'required_hours': getattr(opp, 'required_hours', 0),
            'status': opp.status,
        })
    return JsonResponse({'offers': offers})


from django.db.models import Avg
from internships.models import Application, Internship

@login_required(login_url='frontend:login')
def company_dashboard_json(request):
    """Return aggregate dashboard statistics for the logged-in company."""
    user = request.user
    company = getattr(user, 'company', None)
    is_global_company_admin = user.is_staff or user.is_superuser
    if not company and not is_global_company_admin:
        return JsonResponse({'ok': True, 'activeOffers': 0, 'totalApplicants': 0, 'pendingReview': 0, 'activeInternships': 0, 'avgRating': 0})

    opportunity_filter = {} if is_global_company_admin else {'company': company}
    active_offers = Opportunity.objects.filter(
        **opportunity_filter,
        status=Opportunity.Status.ACTIVE,
    ).count()
    total_applicants = Application.objects.filter(
        **({'opportunity__' + key: value for key, value in opportunity_filter.items()}),
    ).count() if opportunity_filter else Application.objects.count()
    pending_review = Application.objects.filter(
        **({'opportunity__' + key: value for key, value in opportunity_filter.items()}),
        status__in=[Application.Status.SENT, Application.Status.REVIEW],
    ).count() if opportunity_filter else Application.objects.filter(
        status__in=[Application.Status.SENT, Application.Status.REVIEW],
    ).count()
    active_internships = Internship.objects.filter(
        **opportunity_filter,
        status=Internship.Status.IN_PROGRESS,
    ).count() if opportunity_filter else Internship.objects.filter(
        status=Internship.Status.IN_PROGRESS,
    ).count()

    # Acceptance metrics: accepted applications / total applications
    accepted_applications = Application.objects.filter(
        **({'opportunity__' + key: value for key, value in opportunity_filter.items()}),
        status=Application.Status.ACCEPTED,
    ).count() if opportunity_filter else Application.objects.filter(
        status=Application.Status.ACCEPTED,
    ).count()
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
        evaluation_filter = {'internship__company': company} if company else {}
        agg = EvalModel.objects.filter(**evaluation_filter).aggregate(avg=Avg('score'))
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
    if not company and not (user.is_staff or user.is_superuser):
        return JsonResponse({'internships': []})

    internship_filter = {} if user.is_staff or user.is_superuser else {'company': company}
    qs = Internship.objects.filter(
        **internship_filter,
        status=Internship.Status.IN_PROGRESS,
    ).select_related('student__user', 'application__opportunity')
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
    if not company and not (user.is_staff or user.is_superuser):
        return JsonResponse({'applications': []})

    application_filter = {} if user.is_staff or user.is_superuser else {'opportunity__company': company}
    qs = Application.objects.filter(
        **application_filter,
        status__in=[Application.Status.SENT, Application.Status.REVIEW],
    ).select_related(
        'student__user',
        'student__institution',
        'student__career',
        'opportunity__company',
        'opportunity__career',
    ).order_by('-created_at')[:20]
    applications = []
    for app in qs:
        student_name = app.student.user.get_full_name() or app.student.user.username
        applications.append({
            'id': app.id,
            'name': student_name,
            'position': app.opportunity.title if app.opportunity else '',
            'date': app.created_at.date().isoformat(),
            'rating': None,
            'email': app.student.user.email,
            'phone': app.student.phone,
            'institution': app.student.institution.name,
            'career': app.student.career.name,
            'student_code': app.student.student_code,
            'message': app.message,
            'description': app.opportunity.description if app.opportunity else '',
            'modality': app.opportunity.get_modality_display() if app.opportunity else '',
            'vacancies': app.opportunity.vacancies if app.opportunity else 0,
            'required_hours': app.opportunity.required_hours if app.opportunity else 0,
            'requirements': app.opportunity.requirements if app.opportunity else [],
        })

    return JsonResponse({'applications': applications})


@login_required(login_url='frontend:login')
@require_POST
def update_application_status(request, application_id):
    user = request.user
    application = get_object_or_404(Application.objects.select_related('opportunity'), id=application_id)
    if not (user.is_staff or user.is_superuser or getattr(user, 'company_id', None) == application.opportunity.company_id):
        return JsonResponse({'ok': False, 'error': 'No tienes permiso para gestionar esta postulación.'}, status=403)

    status = request.POST.get('status')
    if status not in {Application.Status.ACCEPTED, Application.Status.REJECTED}:
        return JsonResponse({'ok': False, 'error': 'Estado de postulación no válido.'}, status=400)

    application.status = status
    application.save(update_fields=['status'])

    if status == Application.Status.ACCEPTED:
        required_hours = InstitutionConfig.objects.filter(
            institution=application.opportunity.institution,
        ).values_list('required_hours', flat=True).first() or 240
        start_date = timezone.localdate()
        end_date = start_date + timedelta(days=ceil(required_hours / 8))
        supervisor, _ = Supervisor.objects.get_or_create(
            company=application.opportunity.company,
            full_name=f"Supervisor de {application.opportunity.company.name}",
            defaults={
                'position': 'Supervisor de Pasantías',
                'email': application.opportunity.company.email or 'supervisor@skillbridge.local',
                'phone': application.opportunity.company.phone,
                'is_active': True,
            },
        )
        internship, _ = Internship.objects.get_or_create(
            application=application,
            defaults={
                'student': application.student,
                'company': application.opportunity.company,
                'supervisor': supervisor,
                'start_date': start_date,
                'end_date': end_date,
                'status': Internship.Status.IN_PROGRESS,
                'total_hours': 0,
            },
        )
        if internship.end_date != end_date:
            internship.end_date = end_date
            internship.save(update_fields=['end_date'])

    return JsonResponse({
        'ok': True,
        'status': application.get_status_display(),
        'application_id': application.id,
    })


@login_required(login_url='frontend:login')
def student_dashboard_json(request):
    """Return basic dashboard counts for the logged-in student as JSON."""
    user = request.user

    # Total available opportunities (active)
    try:
        opportunities = Opportunity.objects.filter(status=Opportunity.Status.ACTIVE).count()
    except Exception:
        opportunities = 0

    # Applications for this student
    try:
        applications = Application.objects.filter(student__user=user).count()
    except Exception:
        applications = 0

    # Accepted applications for this student
    try:
        accepted = Application.objects.filter(student__user=user, status=Application.Status.ACCEPTED).count()
    except Exception:
        accepted = 0

    return JsonResponse({'stats': {'opportunities': opportunities, 'applications': applications, 'accepted': accepted}})


@login_required(login_url='frontend:login')
@require_POST
def toggle_offer_status_view(request, offer_id):
    opp = Opportunity.objects.filter(id=offer_id).first()
    if not opp:
        messages.error(request, 'La oferta solicitada no existe.')
        return redirect('frontend:company-offers')

    user = request.user
    if not (user.is_staff or user.is_superuser or getattr(user, 'company_id', None) == opp.company_id):
        messages.error(request, 'No tienes permisos para cambiar esta oferta.')
        return redirect('frontend:company-offers')

    if opp.status == Opportunity.Status.ACTIVE:
        opp.status = Opportunity.Status.PAUSED
        message = 'Oferta marcada como inactiva. Ya no aparecerá para los pasantes.'
    elif opp.status == Opportunity.Status.PAUSED:
        opp.status = Opportunity.Status.ACTIVE
        message = 'Oferta marcada como activa. Ahora aparecerá para los pasantes.'
    else:
        messages.error(request, 'Solo puedes activar o inactivar ofertas no canceladas.')
        return redirect('frontend:company-offers')

    opp.save(update_fields=['status'])
    messages.success(request, message)
    return redirect('frontend:company-offers')


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
