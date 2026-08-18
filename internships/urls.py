from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import OpportunityViewSet, StudentDashboardAPIView, StudentProfileViewSet

router = DefaultRouter()
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')
router.register(r'student-profile', StudentProfileViewSet, basename='studentprofile')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', StudentDashboardAPIView.as_view(), name='student-dashboard'),
]
