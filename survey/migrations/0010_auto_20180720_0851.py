# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-07-20 05:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0009_auto_20180719_1830'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contextset',
            name='derivation',
        ),
        migrations.AddField(
            model_name='context',
            name='derivation',
            field=models.TextField(default=''),
        ),
    ]
