from rest_framework import serializers
from .models import Opportunity, Application, Internship, Activity
from companies.models import Company
from institutions.models import Institution, TechnicalCareer
from django.utils import timezone


class OpportunitySerializer(serializers.ModelSerializer):
    institution = serializers.PrimaryKeyRelatedField(queryset=Institution.objects.all(), required=False)
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=False)
    career = serializers.PrimaryKeyRelatedField(queryset=TechnicalCareer.objects.all(), required=False)

    # Extra read-only fields to make frontend rendering simpler
    company_name = serializers.SerializerMethodField()
    company_description = serializers.SerializerMethodField()
    required_hours = serializers.SerializerMethodField()
    applicants_count = serializers.SerializerMethodField()
    area = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = Opportunity
        fields = [
            'id', 'institution', 'company', 'career', 'title', 'description', 'requirements',
            'vacancies', 'modality', 'deadline', 'status', 'created_at',
            'company_name', 'company_description', 'required_hours', 'applicants_count', 'area', 'location'
        ]
        read_only_fields = ['id', 'created_at', 'status', 'company_name', 'company_description', 'required_hours', 'applicants_count', 'area', 'location']

    def get_company_name(self, obj):
        return obj.company.name if getattr(obj, 'company', None) else ''

    def get_company_description(self, obj):
        # Company model doesn't have 'description' field; use legal_name or website as fallback
        if getattr(obj, 'company', None):
            return getattr(obj.company, 'legal_name', '') or getattr(obj.company, 'website', '') or ''
        return ''

    def get_required_hours(self, obj):
        return getattr(obj, 'required_hours', 0) or 0

    def get_applicants_count(self, obj):
        return obj.applications.count() if hasattr(obj, 'applications') else 0

    def get_area(self, obj):
        return getattr(obj.career, 'name', '') if getattr(obj, 'career', None) else ''

    def get_location(self, obj):
        return getattr(obj.institution, 'name', '') if getattr(obj, 'institution', None) else ''

    def validate(self, data):
        # Ensure deadline present
        if not data.get('deadline') and not self.instance:
            raise serializers.ValidationError({'deadline': 'La fecha límite es obligatoria.'})
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        # Determine company
        company = validated_data.pop('company', None)
        if not company and user and hasattr(user, 'company') and user.company:
            company = user.company
        if not company:
            raise serializers.ValidationError({'company': 'La oferta debe estar asociada a una empresa.'})

        # Check company validated
        if not company.is_validated:
            raise serializers.ValidationError({'company': 'La empresa no está validada para publicar ofertas.'})

        # Institution and career: allow defaults if not provided
        institution = validated_data.pop('institution', None)
        if not institution:
            institution, _ = Institution.objects.get_or_create(name='Plataforma Pública')

        career = validated_data.pop('career', None)
        if not career:
            career, _ = TechnicalCareer.objects.get_or_create(institution=institution, name='General')

        opp = Opportunity.objects.create(
            institution=institution,
            company=company,
            career=career,
            **validated_data
        )
        return opp

    def update(self, instance, validated_data):
        # Prevent changing company via update
        validated_data.pop('company', None)
        return super().update(instance, validated_data)


class ApplicationSerializer(serializers.ModelSerializer):
    opportunity = serializers.PrimaryKeyRelatedField(queryset=Opportunity.objects.filter(status='ACTIVE'))

    class Meta:
        model = Application
        fields = ['id', 'opportunity', 'student', 'message', 'status', 'created_at']
        read_only_fields = ['id', 'student', 'status', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError({'detail': 'Authentication required.'})
        student = getattr(user, 'student_profile', None)
        if not student:
            raise serializers.ValidationError({'detail': 'Current user is not a student.'})
        # Ensure uniqueness handled by model constraint; let DB raise if duplicate
        validated_data['student'] = student
        app = Application.objects.create(**validated_data)
        return app


class InternshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Internship
        fields = ['id', 'application', 'student', 'company', 'supervisor', 'start_date', 'end_date', 'status', 'total_hours', 'created_at']
        read_only_fields = ['id', 'created_at']


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['id', 'internship', 'date', 'description', 'hours', 'validated', 'validated_at', 'validation_comment', 'validated_by', 'created_by', 'created_at']
        read_only_fields = [
            'id', 'validated', 'validated_at', 'validation_comment',
            'validated_by', 'created_by', 'created_at',
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        student = getattr(user, 'student_profile', None)
        if not student or attrs['internship'].student_id != student.id:
            raise serializers.ValidationError(
                {'internship': 'Solo puedes registrar horas de tu propia pasantía.'}
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError({'detail': 'Authentication required.'})
        validated_data['created_by'] = user
        activity = Activity.objects.create(**validated_data)
        return activity