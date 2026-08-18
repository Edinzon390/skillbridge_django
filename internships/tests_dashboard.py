from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from institutions.models import Institution, TechnicalCareer
from companies.models import Company, Supervisor
from internships.models import StudentProfile, Opportunity, Application, Internship, Activity, Evaluation, Evidence
from django.utils import timezone

User = get_user_model()

class StudentDashboardAPITest(TestCase):
    def setUp(self):
        # Create user and related objects
        self.admin = User.objects.create_user(username='tadmin', email='tadmin@example.com', password='tadminpass', role='SUPER_ADMIN')
        self.company = Company.objects.create(name='TestCo', email='test@example.com', is_validated=True)
        self.inst = Institution.objects.create(name='Test University')
        self.career = TechnicalCareer.objects.create(institution=self.inst, name='Test Career')
        self.sup_user = User.objects.create_user(username='sup', password='suppass', role='COMPANY_SUPERVISOR')
        self.sup = Supervisor.objects.create(company=self.company, full_name='Sup Test', email='sup@test.com')

        self.student_user = User.objects.create_user(username='stu', password='stupass', role='STUDENT')
        self.student_profile = StudentProfile.objects.create(user=self.student_user, institution=self.inst, career=self.career, student_code='TS1', is_eligible=True)

        # Create an opportunity and application
        self.opp = Opportunity.objects.create(institution=self.inst, company=self.company, career=self.career, title='Test Opp', description='x', requirements=[], vacancies=1, modality='REMOTE', deadline=timezone.now() + timezone.timedelta(days=10), status='ACTIVE')
        self.app = Application.objects.create(opportunity=self.opp, student=self.student_profile, message='hola')
        self.intern = Internship.objects.create(application=self.app, student=self.student_profile, company=self.company, supervisor=self.sup, status='IN_PROGRESS')
        Activity.objects.create(internship=self.intern, description='act', hours=2, created_by=self.admin)
        Evaluation.objects.create(internship=self.intern, score=4.0, criteria={}, comments='ok', result='APPROVED', evaluated_by=self.admin)
        Evidence.objects.create(internship=self.intern, uploaded_by=self.admin, description='evi')

        self.client = APIClient()

    def test_dashboard_requires_auth(self):
        url = reverse('student-dashboard')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 401)

    def test_dashboard_returns_data_for_student(self):
        # login to obtain token
        token_url = '/api/accounts/token/'
        resp = self.client.post(token_url, {'username': 'stu', 'password': 'stupass'}, format='json')
        self.assertEqual(resp.status_code, 200)
        access = resp.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        url = reverse('student-dashboard')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('student_profile', data)
        # verify non-empty lists
        self.assertTrue(len(data.get('applications', [])) >= 1)
        self.assertTrue(len(data.get('internships', [])) >= 1)
        self.assertTrue(len(data.get('activities', [])) >= 1)
        self.assertTrue(len(data.get('evaluations', [])) >= 1)
        self.assertTrue(len(data.get('evidences', [])) >= 1)
