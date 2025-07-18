# Generated by Django 5.1.8 on 2025-05-01 07:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_transaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='funding_goal',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='transaction',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='main.project'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='amount_eth',
            field=models.DecimalField(decimal_places=5, max_digits=10),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='tx_hash',
            field=models.CharField(max_length=66, unique=True),
        ),
    ]
