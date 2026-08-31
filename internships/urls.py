from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import OpportunityViewSet, ApplicationViewSet, InternshipViewSet, ActivityViewSet

router = DefaultRouter()
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'internships', InternshipViewSet, basename='internship')
router.register(r'activities', ActivityViewSet, basename='activity')

urlpatterns = [
    path('', include(router.urls)),
]
