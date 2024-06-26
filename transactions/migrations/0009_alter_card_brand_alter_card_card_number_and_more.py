# Generated by Django 4.1.4 on 2024-04-12 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0008_alter_transaction_account_number_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='brand',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='card',
            name='card_number',
            field=models.CharField(max_length=160),
        ),
        migrations.AlterField(
            model_name='card',
            name='cvv',
            field=models.CharField(max_length=40),
        ),
        migrations.AlterField(
            model_name='card',
            name='expiry_month',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='card',
            name='expiry_year',
            field=models.CharField(max_length=20),
        ),
    ]
