# Generated by Django 4.2.13 on 2024-05-22 21:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0019_escrow_accepted_escrow_answered'),
    ]

    operations = [
        migrations.AddField(
            model_name='escrow',
            name='make_payment',
            field=models.BooleanField(default=False),
        ),
    ]
