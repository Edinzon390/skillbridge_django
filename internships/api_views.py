from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Opportunity, Application, Internship, Activity
from .serializers import OpportunitySerializer, ApplicationSerializer, InternshipSerializer, ActivitySerializer
from accounts.models import Role
from django.utils import timezone


class IsCompanyOrReadOnly(permissions.BasePermission):
    """Allow read-only to anyone; write only to authenticated company users or staff."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        # Allow staff/superuser
        if request.user.is_staff or request.user.is_superuser:
            return True
        return getattr(request.user, 'role', None) == Role.COMPANY


class IsCompanyOwnerOrAdmin(permissions.BasePermission):
    """Allow modifications only if the user belongs to the company owning the opportunity or is admin."""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        user_company = getattr(user, 'company', None)
        return user_company is not None and getattr(obj, 'company_id', getattr(obj, 'company', None)) == user_company.id


class OpportunityViewSet(viewsets.ModelViewSet):
    queryset = Opportunity.objects.all().order_by('-created_at')
    serializer_class = OpportunitySerializer
    permission_classes = [IsCompanyOrReadOnly, IsCompanyOwnerOrAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        # Optional filtering: active only, by company, by career, by area, search by title
        status = self.request.query_params.get('status')
        company = self.request.query_params.get('company')
        career = self.request.query_params.get('career')
        q = self.request.query_params.get('q')
        if status:
            qs = qs.filter(status__iexact=status)
        if company:
            qs = qs.filter(company_id=company)
        if career:
            qs = qs.filter(career_id=career)
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

    def perform_create(self, serializer):
        # serializer.create will use request.user.company when appropriate
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def my(self, request):
        # Return offers for current user's company
        user = request.user
        if not user or not user.is_authenticated or not getattr(user, 'company', None):
            return Response([], status=status.HTTP_200_OK)
        qs = self.get_queryset().filter(company=user.company)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all().order_by('-created_at')
    serializer_class = ApplicationSerializer

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        # For accept/reject actions, ensure company owner or admin
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Application.objects.none()
        # Students see their applications; company staff see applications for their company's opportunities
        if getattr(user, 'role', None) == Role.COMPANY and getattr(user, 'company', None):
            return Application.objects.filter(opportunity__company=user.company).order_by('-created_at')
        student = getattr(user, 'student_profile', None)
        if student:
            return Application.objects.filter(student=student).order_by('-created_at')
        return Application.objects.none()

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def accept(self, request, pk=None):
        app = self.get_object()
        user = request.user
        # Only company owning the opportunity or staff can accept
        if not (user.is_staff or user.is_superuser or (hasattr(user, 'company') and user.company and user.company.id == app.opportunity.company_id)):
            return Response({'detail': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        if app.status == Application.Status.ACCEPTED:
            return Response({'detail': 'Ya aceptada'}, status=status.HTTP_400_BAD_REQUEST)
        app.status = Application.Status.ACCEPTED
        app.save()
        # Create Internship
        company = app.opportunity.company
        supervisor = None
        if company:
            sup_qs = getattr(company, 'supervisors', None)
            if sup_qs and sup_qs.exists():
                supervisor = sup_qs.first()
            else:
                # create a placeholder supervisor using company contact info
                from companies.models import Supervisor
                email = company.email or f'no-reply@{company.name.replace(" ","").lower()}.local'
                supervisor = Supervisor.objects.create(company=company, full_name=company.name, email=email)
        internship = Internship.objects.create(
            application=app,
            student=app.student,
            company=company,
            supervisor=supervisor,
            start_date=timezone.now().date(),
            status=Internship.Status.IN_PROGRESS,
            total_hours=0
        )
        return Response({'ok': True, 'internship_id': internship.id}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        app = self.get_object()
        user = request.user
        if not (user.is_staff or user.is_superuser or (hasattr(user, 'company') and user.company and user.company.id == app.opportunity.company_id)):
            return Response({'detail': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        if app.status == Application.Status.REJECTED:
            return Response({'detail': 'Ya rechazada'}, status=status.HTTP_400_BAD_REQUEST)
        app.status = Application.Status.REJECTED
        app.save()
        return Response({'ok': True}, status=status.HTTP_200_OK)


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all().order_by('-created_at')
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Activity.objects.none()
        # Students see activities for their internships; company users can see activities for their company
        if getattr(user, 'role', None) == Role.COMPANY and getattr(user, 'company', None):
            return Activity.objects.filter(internship__company=user.company).order_by('-created_at')
        student = getattr(user, 'student_profile', None)
        if student:
            return Activity.objects.filter(internship__student=student).order_by('-created_at')
        return Activity.objects.none()

    def perform_create(self, serializer):
        serializer.save()


class InternshipViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Internship.objects.all().order_by('-created_at')
    serializer_class = InternshipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Internship.objects.none()
        if getattr(user, 'role', None) == Role.COMPANY and getattr(user, 'company', None):
            return Internship.objects.filter(company=user.company).order_by('-created_at')
        student = getattr(user, 'student_profile', None)
        if student:
            return Internship.objects.filter(student=student).order_by('-created_at')
        return Internship.objects.none()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_hours(self, request, pk=None):
        internship = self.get_object()
        # Only student of internship or company supervisor/staff can add hours via activity
        user = request.user
        student = getattr(user, 'student_profile', None)
        if not (user.is_staff or user.is_superuser or (student and internship.student_id == student.id) or (hasattr(user, 'company') and user.company and internship.company_id == user.company.id)):
            return Response({'detail': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        hours = request.data.get('hours')
        description = request.data.get('description', '')
        if not hours:
            return Response({'detail': 'hours required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            hours_val = float(hours)
        except Exception:
            return Response({'detail': 'invalid hours'}, status=status.HTTP_400_BAD_REQUEST)
        activity = Activity.objects.create(internship=internship, hours=hours_val, description=description, created_by=user)
        internship.total_hours = internship.total_hours + int(hours_val)
        internship.save()
        return Response({'ok': True, 'activity_id': activity.id}, status=status.HTTP_201_CREATED)
