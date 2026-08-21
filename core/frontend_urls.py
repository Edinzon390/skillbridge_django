from django.urls import path
from . import frontend_views
from .frontend_actions_clean import register_submit, create_offer_view, edit_offer_view, company_profile_view, save_chat_message, company_offers_json

app_name = 'frontend'

urlpatterns = [
    # HOME
    path('', frontend_views.home, name='home'),
    path('help/', frontend_views.help_page, name='help'),
    
    # AUTH
    path('login/', frontend_views.login_view, name='login'),
    path('register/', register_submit, name='register'),
    path('logout/', frontend_views.logout_view, name='logout'),
    path('password-reset/', frontend_views.password_reset_view, name='password-reset'),
    
    # STUDENT
    path('dashboard/', frontend_views.student_dashboard, name='student-dashboard'),
    path('internships/', frontend_views.internships_list, name='internships'),
    path('applications/', frontend_views.my_applications, name='my-applications'),
    path('my-internships/', frontend_views.my_internships, name='my-internships'),
    path('internship/<int:internship_id>/', frontend_views.view_internship, name='view-internship'),
    path('internship/<int:internship_id>/log-hours/', frontend_views.log_hours, name='log-hours'),
    path('profile/', frontend_views.student_profile, name='profile'),
    path('student/dashboard/', frontend_views.student_dashboard, name='student-dashboard-alt'),
    path('student/opportunities/', frontend_views.internships_list, name='student-opportunities'),
    path('student/opportunities/<int:internship_id>/', frontend_views.view_internship, name='student-opportunity-detail'),
    path('student/applications/', frontend_views.my_applications, name='student-applications'),
    path('student/my-internships/', frontend_views.my_internships, name='student-my-internships'),
    path('student/internship/<int:internship_id>/', frontend_views.view_internship, name='student-internship-detail'),
    path('student/internship/<int:internship_id>/log-hours/', frontend_views.log_hours, name='student-log-hours'),
    path('student/profile/', frontend_views.student_profile, name='student-profile'),
    
    # COMPANY
    path('company/dashboard/', frontend_views.company_dashboard, name='company-dashboard'),
    path('company/offers/', frontend_views.company_offers, name='company-offers'),
    path('company/offers/json/', company_offers_json, name='company-offers-json'),
    path('company/offers/create/', create_offer_view, name='create-offer'),
    path('company/offers/<int:offer_id>/edit/', edit_offer_view, name='edit-offer'),
    path('company/offers/<int:offer_id>/', edit_offer_view, name='company-offer-detail'),
    path('company/offers/<int:offer_id>/applicants/', frontend_views.applicants_view, name='company-offer-applicants'),
    path('company/internships/', frontend_views.company_internships, name='company-internships'),
    path('company/internships/<int:internship_id>/', frontend_views.company_internships, name='company-internship-detail'),
    path('company/internships/<int:internship_id>/evaluate/', frontend_views.hours_validation, name='company-internship-evaluate'),
    path('company/hours-validation/', frontend_views.hours_validation, name='hours-validation'),
    path('company/applicants/', frontend_views.applicants_view, name='applicants'),
    path('company/profile/', company_profile_view, name='company-profile'),
    path('support/save-message/', save_chat_message, name='save-chat-message'),
    
    # ADMIN
    path('administration/dashboard/', frontend_views.admin_dashboard, name='admin-dashboard'),
    path('administration/students/', frontend_views.students_management, name='students-management'),
    path('administration/companies/', frontend_views.companies_management, name='companies-management'),
    path('administration/internships/', frontend_views.internships_monitoring, name='internships-monitoring'),
    path('administration/institutions/', frontend_views.institutions_view, name='institutions'),
    path('administration/users/', frontend_views.users_management, name='users-management'),
    path('administration/export/', frontend_views.export_report, name='export-report'),
    
    # API
    path('api/user-roles/', frontend_views.get_user_roles, name='api-user-roles'),

    path('student/profile/', frontend_views.student_profile, name='student-profile'),
    path('student/careers/<int:institution_id>/', frontend_views.careers_by_institution_json, name='careers-by-institution'),
]
