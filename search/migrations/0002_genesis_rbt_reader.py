# Generated by Django 4.2.3 on 2023-09-13 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='genesis',
            name='rbt_reader',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
