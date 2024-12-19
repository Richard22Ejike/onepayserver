# Generated by Django 4.2.13 on 2024-11-26 11:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('username', models.CharField(default='', max_length=100, verbose_name='Username')),
                ('email', models.EmailField(default='', max_length=255, unique=True, verbose_name='Email Address')),
                ('first_name', models.CharField(default='', max_length=100, verbose_name='First Name')),
                ('last_name', models.CharField(default='', max_length=100, verbose_name='last name')),
                ('phone_number', models.CharField(default='', max_length=11, unique=True)),
                ('image', models.CharField(default='', max_length=255)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=False)),
                ('is_verified', models.BooleanField(default=False)),
                ('status', models.BooleanField(default=False)),
                ('customer_id', models.CharField(default='', max_length=100)),
                ('account_id', models.CharField(default='', max_length=100)),
                ('organization_id', models.CharField(default='', max_length=100)),
                ('customer_type', models.CharField(default='', max_length=100)),
                ('bvn', models.CharField(default='', max_length=100)),
                ('account_number', models.CharField(default='', max_length=100)),
                ('escrow_fund', models.FloatField(default=0.0)),
                ('date_of_birth', models.CharField()),
                ('bank_name', models.CharField(default='', max_length=100)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('bank_pin', models.CharField(default='', max_length=10)),
                ('balance', models.FloatField(default=0.0, max_length=100)),
                ('device_id', models.CharField(default='', max_length=100)),
                ('street', models.CharField(default='', max_length=100)),
                ('city', models.CharField(default='', max_length=100)),
                ('state', models.CharField(default='', max_length=100)),
                ('country', models.CharField(default='', max_length=100)),
                ('postal_code', models.CharField(default='', max_length=100)),
                ('access_token', models.CharField(default='', max_length=800)),
                ('refresh_token', models.CharField(default='', max_length=800)),
                ('notification_number', models.IntegerField(default=0)),
                ('kyc_tier', models.IntegerField(default=0)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Customers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=255, unique=True, verbose_name='Email Address')),
                ('first_name', models.CharField(max_length=100, verbose_name='First Name')),
                ('last_name', models.CharField(max_length=100, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('last_login', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='OneTimeOtp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(default='', max_length=100)),
                ('code', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='OneTimePassword',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=6, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
