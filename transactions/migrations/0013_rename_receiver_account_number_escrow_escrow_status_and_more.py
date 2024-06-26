# Generated by Django 4.1.4 on 2024-05-09 18:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0012_escrow'),
    ]

    operations = [
        migrations.RenameField(
            model_name='escrow',
            old_name='receiver_account_number',
            new_name='escrow_Status',
        ),
        migrations.RenameField(
            model_name='escrow',
            old_name='receiver_bank_code',
            new_name='estimated_days',
        ),
        migrations.RenameField(
            model_name='escrow',
            old_name='receiver_name',
            new_name='milestone',
        ),
        migrations.RemoveField(
            model_name='escrow',
            name='end_time',
        ),
        migrations.RemoveField(
            model_name='escrow',
            name='environment',
        ),
        migrations.RemoveField(
            model_name='escrow',
            name='organization_id',
        ),
        migrations.RemoveField(
            model_name='escrow',
            name='start_time',
        ),
        migrations.AddField(
            model_name='escrow',
            name='number_milestone',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='escrow',
            name='payment_type',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='escrow',
            name='role',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='escrow',
            name='role_paying',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='escrow',
            name='transaction_fee',
            field=models.IntegerField(default=0),
        ),
    ]
