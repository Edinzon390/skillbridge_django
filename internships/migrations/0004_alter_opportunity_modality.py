from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("internships", "0003_opportunity_required_hours"),
    ]

    operations = [
        migrations.AlterField(
            model_name="opportunity",
            name="modality",
            field=models.CharField(
                choices=[
                    ("PRESENTIAL", "Presencial (oficina)"),
                    ("REMOTE", "Remoto (virtual)"),
                    ("HYBRID", "Híbrido (mixto)"),
                ],
                max_length=20,
            ),
        ),
    ]
