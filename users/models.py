from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AbstractUser
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken

from .manager import UserManager


# Create your models here.
class Customers(models.Model):
    email = models.EmailField(max_length=255, unique=True, verbose_name=_("Email Address"))
    first_name = models.CharField(max_length=100, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=100, verbose_name=_("last name"))
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def tokens(self):
        pass


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=100, verbose_name=_("Username"), default='')
    email = models.EmailField(max_length=255, unique=True, verbose_name=_("Email Address"), default='')
    first_name = models.CharField(max_length=100, verbose_name=_("First Name"), default='')
    last_name = models.CharField(max_length=100, verbose_name=_("last name"), default='')
    phone_number = models.CharField(max_length=11, default='', unique=True)
    image = models.CharField(max_length=255, default='')
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    status = models.BooleanField(default=False)
    customer_id = models.CharField(max_length=100, default='')
    account_id = models.CharField(max_length=100, default='')
    organization_id = models.CharField(max_length=100, default='')
    customer_type = models.CharField(default='', max_length=100)
    bvn = models.CharField(max_length=100, default='')
    account_number = models.CharField(max_length=100, default='')
    escrow_fund = models.FloatField(default=0.0)
    bank_name = models.CharField(default='', max_length=100)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    bank_pin = models.CharField(max_length=10, default='')
    balance = models.FloatField(max_length=100, default=0.0)
    device_id = models.CharField(max_length=100, default='')
    street = models.CharField(max_length=100, default='')
    city = models.CharField(max_length=100, default='')
    state = models.CharField(max_length=100, default='')
    country = models.CharField(max_length=100, default='')
    postal_code = models.CharField(max_length=100, default='')
    access_token = models.CharField(max_length=100, default='')
    refresh_token = models.CharField(max_length=100, default='')
    notification_number = models.IntegerField(default=0)
    kyc_tier = models.IntegerField(default=0)
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }


class OneTimePassword(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name} passcode"


class OneTimeOtp(models.Model):
    key = models.CharField(default='', max_length=100, )
    code = models.CharField(max_length=6, )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.key} passcode"
