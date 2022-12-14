# Generated by Django 2.2.15 on 2022-09-14 04:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('player_id', models.IntegerField()),
                ('name', models.CharField(max_length=100)),
                ('server_id', models.CharField(max_length=10)),
                ('planets', models.BinaryField()),
            ],
        ),
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.IntegerField()),
                ('total', models.BinaryField()),
                ('economy', models.BinaryField()),
                ('research', models.BinaryField()),
                ('military', models.BinaryField()),
                ('military_built', models.BinaryField()),
                ('military_destroyed', models.BinaryField()),
                ('military_lost', models.BinaryField()),
                ('honor', models.BinaryField()),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ogame.Player')),
            ],
        ),
    ]
