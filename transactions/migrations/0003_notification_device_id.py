# Generated by Django 4.2.13 on 2024-07-18 16:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='device_id',
            field=models.CharField(default='', max_length=100),
        ),
    ]