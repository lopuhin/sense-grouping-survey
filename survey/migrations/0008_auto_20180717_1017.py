# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-07-17 07:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0007_participant_cs_to_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='sex',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='survey.Sex', verbose_name='Пол'),
        ),
    ]
