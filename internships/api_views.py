from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Opportunity
from .serializers import OpportunitySerializer
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
