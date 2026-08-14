from rest_framework import serializers
from .models import Opportunity
from companies.models import Company
from institutions.models import Institution, TechnicalCareer


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
