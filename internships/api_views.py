from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from .models import (
    Opportunity, StudentProfile, Application, Internship,
    Activity, Evaluation, Evidence
)
from .serializers import (
    OpportunitySerializer, StudentProfileSerializer, ApplicationSerializer,
    InternshipSerializer, ActivitySerializer, EvaluationSerializer, EvidenceSerializer
)
from accounts.models import Role


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
        return user_company is not None and obj.company_id == user_company.id


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


class StudentDashboardAPIView(APIView):
    """Consolidated student dashboard data for the authenticated student."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        student_profile = getattr(user, 'student_profile', None)
        if not student_profile:
            return Response({'detail': 'Perfil de estudiante no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Applications
        applications = Application.objects.filter(student=student_profile).order_by('-created_at')
        applications_data = ApplicationSerializer(applications, many=True).data

        # Internships
        internships = Internship.objects.filter(student=student_profile).order_by('-created_at')
        internships_data = InternshipSerializer(internships, many=True).data

        # Recent activities (last 20)
        activities = Activity.objects.filter(internship__student=student_profile).order_by('-date')[:20]
        activities_data = ActivitySerializer(activities, many=True).data

        # Evaluations
        evaluations = Evaluation.objects.filter(internship__student=student_profile)
        evaluations_data = EvaluationSerializer(evaluations, many=True).data

        # Evidences (last 10)
        evidences = Evidence.objects.filter(internship__student=student_profile).order_by('-created_at')[:10]
        evidences_data = EvidenceSerializer(evidences, many=True).data

        # Recommended opportunities: active and matching career (limit 10)
        recommended_qs = Opportunity.objects.filter(status=Opportunity.Status.ACTIVE, career=student_profile.career).order_by('-created_at')[:10]
        recommended_data = OpportunitySerializer(recommended_qs, many=True).data

        dashboard = {
            'student_profile': StudentProfileSerializer(student_profile).data,
            'applications': applications_data,
            'internships': internships_data,
            'activities': activities_data,
            'evaluations': evaluations_data,
            'evidences': evidences_data,
            'recommended_opportunities': recommended_data,
        }

        return Response(dashboard, status=status.HTTP_200_OK)


class StudentProfileViewSet(viewsets.ModelViewSet):
    """ViewSet to retrieve and update the authenticated student's profile."""
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # staff can view all
        if user.is_staff or user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # enforce ownership
        if serializer.instance.user != self.request.user and not (self.request.user.is_staff or self.request.user.is_superuser):
            raise permissions.PermissionDenied('No puedes modificar este perfil')
        serializer.save()
