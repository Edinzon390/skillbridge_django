from rest_framework.permissions import BasePermission
from accounts.models import Role

class HasRole(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and (request.user.is_superuser or request.user.role in self.allowed_roles)
        )

class IsCoordinator(HasRole):
    allowed_roles = (Role.COORDINATOR, Role.INSTITUTION_ADMIN, Role.SUPER_ADMIN)

class IsCompanyUser(HasRole):
    allowed_roles = (Role.COMPANY, Role.COMPANY_SUPERVISOR)

class IsStudent(HasRole):
    allowed_roles = (Role.STUDENT,)

class IsTutor(HasRole):
    allowed_roles = (Role.TUTOR, Role.COORDINATOR, Role.INSTITUTION_ADMIN, Role.SUPER_ADMIN)
