# Generated by Django 3.0 on 2021-04-29 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0004_transaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='payment_status',
            field=models.CharField(default='pending', max_length=100),
        ),
    ]
