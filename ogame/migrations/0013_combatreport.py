# Generated by Django 2.2.15 on 2022-10-07 04:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ogame', '0012_player_rank'),
    ]

    operations = [
        migrations.CreateModel(
            name='CombatReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.TextField()),
                ('title', models.TextField()),
                ('date', models.DateField(null=True)),
                ('winner', models.CharField(blank=True, max_length=50, null=True)),
                ('attackers', models.BinaryField(null=True)),
                ('defenders', models.BinaryField(null=True)),
            ],
        ),
    ]
