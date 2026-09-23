from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='object_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]