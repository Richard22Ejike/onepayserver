# Generated by Django 4.1.4 on 2024-04-24 00:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0011_card_linked_alter_card_pin'),
    ]

    operations = [
        migrations.CreateModel(
            name='Escrow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_id', models.CharField(default='', max_length=100)),
                ('customer_id', models.CharField(default='', max_length=100)),
                ('organization_id', models.CharField(default='', max_length=84)),
                ('environment', models.CharField(default='', max_length=10)),
                ('escrow_description', models.CharField(default='', max_length=255)),
                ('escrow_name', models.CharField(default='', max_length=255)),
                ('receiver_name', models.CharField(default='', max_length=100)),
                ('receiver_account_number', models.CharField(default='', max_length=100)),
                ('receiver_bank_code', models.CharField(default='', max_length=100)),
                ('sender_name', models.CharField(default='', max_length=80)),
                ('receiver_email', models.EmailField(blank=True, default='', max_length=100)),
                ('currency', models.CharField(default='NGN', max_length=10)),
                ('link_url', models.URLField(default='')),
                ('amount', models.IntegerField(default=0)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('update_at', models.DateTimeField(auto_now=True)),
                ('is_disabled', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Escrow',
                'verbose_name_plural': 'Escrow',
            },
        ),
    ]
