from rest_framework import serializers
from .models import (
    Opportunity, StudentProfile, Application, Internship,
    Activity, Evaluation, Evidence
)
from companies.models import Company, Supervisor
from institutions.models import Institution, TechnicalCareer
from accounts.models import User


class OpportunitySerializer(serializers.ModelSerializer):
    institution = serializers.PrimaryKeyRelatedField(queryset=Institution.objects.all(), required=False)
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=False)
    career = serializers.PrimaryKeyRelatedField(queryset=TechnicalCareer.objects.all(), required=False)

    class Meta:
        model = Opportunity
        fields = [
            'id', 'institution', 'company', 'career', 'title', 'description', 'requirements',
            'vacancies', 'modality', 'deadline', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'status']

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


class StudentProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    institution_id = serializers.IntegerField(source='institution.id', required=False, allow_null=True)
    career_id = serializers.IntegerField(source='career.id', required=False, allow_null=True)
    cv = serializers.FileField(allow_null=True, required=False)
    portfolio = serializers.FileField(allow_null=True, required=False)
    skills = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'user_id', 'username', 'student_code', 'phone', 'bio', 'skills', 'cv', 'portfolio',
            'is_eligible', 'institution_id', 'career_id', 'created_at'
        ]
        read_only_fields = ['id', 'user_id', 'username', 'is_eligible', 'created_at']

    def update(self, instance, validated_data):
        # Handle nested source fields for institution/career if provided as ids
        institution_data = validated_data.pop('institution', None)
        career_data = validated_data.pop('career', None)
        if institution_data:
            from institutions.models import Institution
            try:
                inst = Institution.objects.get(id=institution_data.get('id'))
                instance.institution = inst
            except Exception:
                pass
        if career_data:
            from institutions.models import TechnicalCareer
            try:
                career = TechnicalCareer.objects.get(id=career_data.get('id'))
                instance.career = career
            except Exception:
                pass

        # Files and simple fields
        for attr in ('student_code', 'phone', 'bio', 'skills', 'cv', 'portfolio'):
            if attr in validated_data:
                setattr(instance, attr, validated_data.get(attr))
        instance.save()
        return instance

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError('Authentication required to create profile')
        validated_data['user'] = user
        return super().create(validated_data)


class ApplicationSerializer(serializers.ModelSerializer):
    opportunity = OpportunitySerializer(read_only=True)
    opportunity_id = serializers.PrimaryKeyRelatedField(queryset=Opportunity.objects.all(), source='opportunity', write_only=True)
    student_id = serializers.IntegerField(source='student.id', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'opportunity', 'opportunity_id', 'student_id', 'message', 'status', 'created_at']
        read_only_fields = ['id', 'created_at', 'status', 'student_id', 'opportunity']


class InternshipSerializer(serializers.ModelSerializer):
    application = ApplicationSerializer(read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.full_name', read_only=True)

    class Meta:
        model = Internship
        fields = ['id', 'application', 'company_name', 'supervisor_name', 'start_date', 'end_date', 'status', 'total_hours', 'created_at']
        read_only_fields = ['id', 'application', 'company_name', 'supervisor_name', 'created_at']


class ActivitySerializer(serializers.ModelSerializer):
    internship_id = serializers.IntegerField(source='internship.id', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Activity
        fields = ['id', 'internship_id', 'date', 'description', 'hours', 'validated', 'validated_at', 'created_by_username', 'created_at']
        read_only_fields = ['id', 'validated_at', 'created_by_username', 'created_at']


class EvaluationSerializer(serializers.ModelSerializer):
    internship_id = serializers.IntegerField(source='internship.id', read_only=True)
    evaluated_by_username = serializers.CharField(source='evaluated_by.username', read_only=True)

    class Meta:
        model = Evaluation
        fields = ['id', 'internship_id', 'score', 'criteria', 'comments', 'result', 'evaluated_by_username', 'evaluated_at']
        read_only_fields = ['id', 'evaluated_by_username', 'evaluated_at']


class EvidenceSerializer(serializers.ModelSerializer):
    internship_id = serializers.IntegerField(source='internship.id', read_only=True)
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)

    class Meta:
        model = Evidence
        fields = ['id', 'internship_id', 'uploaded_by_username', 'file', 'description', 'created_at']
        read_only_fields = ['id', 'uploaded_by_username', 'created_at']
