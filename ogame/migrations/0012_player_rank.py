# Generated by Django 2.2.15 on 2022-10-03 01:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ogame', '0011_auto_20221002_0600'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='rank',
            field=models.IntegerField(null=True),
        ),
    ]
