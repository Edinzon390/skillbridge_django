from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("internships", "0002_activity_validation_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="opportunity",
            name="required_hours",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
