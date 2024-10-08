# Generated by Django 5.1 on 2024-10-07 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_customuser_provider_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='freelancer',
            name='is_technical',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='freelancer',
            name='is_writer',
            field=models.BooleanField(default=False),
        ),
    ]
