from django.db import models
from users.models import User


class NearMeProduct(models.Model):
    product_id = models.CharField(max_length=255, default='', blank=True)
    product_category = models.CharField(max_length=255, default='', blank=True)
    product_name = models.CharField(max_length=255, default='', blank=True)
    product_images = models.JSONField(default=list, blank=True)  # JSONField for list
    customer_id = models.CharField(max_length=255, default='', blank=True)
    video = models.CharField(max_length=255, default='', blank=True)
    title = models.CharField(max_length=255, default='', blank=True)
    location = models.CharField(max_length=255, default='', blank=True)
    lat = models.CharField(max_length=255, default='', blank=True)
    long = models.CharField(max_length=255, default='', blank=True)
    brand = models.CharField(max_length=255, default='', blank=True)
    type = models.CharField(max_length=255, default='', blank=True)
    condition = models.CharField(max_length=255, default='', blank=True)
    description = models.TextField(default='', blank=True)
    price = models.CharField(max_length=255, default='', blank=True)
    delivery = models.CharField(max_length=255, default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255, default='', blank=True)
    chat_id = models.JSONField(default=list, blank=True)
    seller_name = models.CharField(default=255, blank=True)
    seller_image = models.CharField(default=255, blank=True)
    seller_phone_number = models.CharField(default=255, blank=True)
    seller_email = models.CharField(default=255, blank=True)
    seller_id = models.CharField(default=148)

    class Meta:
        ordering = ['created_at']


class ChatNearMeRoom(models.Model):
    chat_id = models.CharField(max_length=255, default='')
    sender_image = models.CharField(blank=True, default='', max_length=255)
    sender_name = models.CharField(blank=True, default='', max_length=255)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    escrow_id = models.IntegerField(default=0)
    sender_by = models.IntegerField(default=0)
    last_message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
