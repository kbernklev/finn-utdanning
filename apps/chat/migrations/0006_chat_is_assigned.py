# Generated by Django 2.0.4 on 2019-04-01 04:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_auto_20190331_1517'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='is_assigned',
            field=models.BooleanField(default=False),
        ),
    ]