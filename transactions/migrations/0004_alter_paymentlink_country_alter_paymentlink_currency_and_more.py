# Generated by Django 4.1.4 on 2024-04-11 10:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0003_remove_paymentlink_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentlink',
            name='country',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='currency',
            field=models.CharField(default='', max_length=10),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='description',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='environment',
            field=models.CharField(default='', max_length=10),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='link_id',
            field=models.CharField(default='', max_length=8),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='name',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='organization_id',
            field=models.CharField(default='', max_length=24),
        ),
    ]
