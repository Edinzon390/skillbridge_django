from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.utils import timezone
from accounts.models import User, Role
from companies.models import Company
from internships.models import Opportunity
from institutions.models import Institution, TechnicalCareer


class OpportunityAPITestCase(APITestCase):
    def setUp(self):
        # Create users
        self.company_user = User.objects.create_user(username='compuser', email='comp@example.com', password='pass', role=Role.COMPANY)
        self.student_user = User.objects.create_user(username='studuser', email='stud@example.com', password='pass', role=Role.STUDENT)
        self.admin_user = User.objects.create_user(username='admin', email='admin@example.com', password='pass', role=Role.SUPER_ADMIN, is_staff=True)

        # Create companies
        self.company = Company.objects.create(name='TestCo', is_validated=True)
        self.company_user.company = self.company
        self.company_user.save()

        self.other_company = Company.objects.create(name='OtherCo', is_validated=True)

        # Institution and career
        self.institution = Institution.objects.create(name='Inst')
        self.career = TechnicalCareer.objects.create(institution=self.institution, name='General')

        # Create an existing opportunity for listing
        self.opp = Opportunity.objects.create(
            institution=self.institution,
            company=self.company,
            career=self.career,
            title='Existing Offer',
            description='Desc',
            requirements=['Python'],
            vacancies=1,
            modality=Opportunity.Modality.PRESENTIAL,
            deadline=timezone.now() + timezone.timedelta(days=30),
            status=Opportunity.Status.ACTIVE
        )

        self.client = APIClient()
        self.list_url = '/api/internships/opportunities/'
        self.my_url = '/api/internships/opportunities/my/'

    def test_public_list_includes_opportunity(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Should return a list (not paginated in default settings here)
        self.assertTrue(any(item['title'] == 'Existing Offer' for item in data))

    def test_company_can_create_opportunity(self):
        self.client.force_authenticate(user=self.company_user)
        payload = {
            'title': 'New Offer',
            'description': 'New desc',
            'requirements': ['Django', 'REST'],
            'vacancies': 1,
            'modality': Opportunity.Modality.REMOTE,
            'deadline': (timezone.now() + timezone.timedelta(days=20)).isoformat()
        }
        resp = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(resp.status_code, 201, resp.content)
        created = Opportunity.objects.filter(title='New Offer').first()
        self.assertIsNotNone(created)
        self.assertEqual(created.company, self.company)

    def test_student_cannot_create_opportunity(self):
        self.client.force_authenticate(user=self.student_user)
        payload = {
            'title': 'Student Offer',
            'description': 'Should fail',
            'requirements': [],
            'vacancies': 1,
            'modality': Opportunity.Modality.REMOTE,
            'deadline': (timezone.now() + timezone.timedelta(days=20)).isoformat()
        }
        resp = self.client.post(self.list_url, payload, format='json')
        self.assertIn(resp.status_code, (403, 401))

    def test_only_owner_can_update(self):
        # Create an opportunity for other company
        other_opp = Opportunity.objects.create(
            institution=self.institution,
            company=self.other_company,
            career=self.career,
            title='Other Offer',
            description='Other',
            requirements=[],
            vacancies=1,
            modality=Opportunity.Modality.PRESENTIAL,
            deadline=timezone.now() + timezone.timedelta(days=10),
            status=Opportunity.Status.ACTIVE
        )

        detail_url = f'{self.list_url}{other_opp.id}/'

        # Company user (not owner) should not update
        self.client.force_authenticate(user=self.company_user)
        resp = self.client.patch(detail_url, {'title': 'Hacked'}, format='json')
        self.assertEqual(resp.status_code, 403)

        # Admin can update
        self.client.force_authenticate(user=self.admin_user)
        resp2 = self.client.patch(detail_url, {'title': 'Admin Updated'}, format='json')
        self.assertIn(resp2.status_code, (200, 204))

        # Owner can update their own
        self.client.force_authenticate(user=self.company_user)
        own_detail = f'{self.list_url}{self.opp.id}/'
        resp3 = self.client.patch(own_detail, {'title': 'Updated Title'}, format='json')
        self.assertIn(resp3.status_code, (200, 204))
        self.opp.refresh_from_db()
        self.assertEqual(self.opp.title, 'Updated Title')

    def test_my_endpoint_returns_company_offers(self):
        # Create another offer for other company
        Opportunity.objects.create(
            institution=self.institution,
            company=self.other_company,
            career=self.career,
            title='Other Company Offer',
            description='Other',
            requirements=[],
            vacancies=1,
            modality=Opportunity.Modality.PRESENTIAL,
            deadline=timezone.now() + timezone.timedelta(days=10),
            status=Opportunity.Status.ACTIVE
        )

        self.client.force_authenticate(user=self.company_user)
        resp = self.client.get(self.my_url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(all(item['company'] == self.company.id for item in data))
