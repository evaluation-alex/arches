# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-12-14 17:03
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('models', '2713_null_boolean_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='mobilesurveymodel',
            name='bounds',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(null=True, srid=4326),
        ),
    ]
