# Generated by Django 3.0 on 2021-04-29 11:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_transaction_cart'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='cart',
            field=models.CharField(default='', max_length=100),
        ),
    ]
