# Generated by Django 4.2.13 on 2024-10-01 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0004_rename_notification_notifications'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentlink',
            name='link_id',
            field=models.CharField(default='', max_length=255),
        ),
    ]
