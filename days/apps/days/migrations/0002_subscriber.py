# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-30 01:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('days', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscriber',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(help_text='An email address to which messages can be sent.', max_length=254, unique=True)),
                ('is_subscribed', models.BooleanField(default=True, help_text='Whether to send emails to this subscriber.')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-modified'],
            },
        ),
    ]
