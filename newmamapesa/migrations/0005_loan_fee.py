# Generated by Django 5.0.2 on 2024-03-07 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newmamapesa', '0004_loantransaction_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='loan',
            name='fee',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]