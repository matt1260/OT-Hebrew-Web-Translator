# Generated by Django 4.1.7 on 2023-03-09 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BibleVerse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('book', models.CharField(max_length=50)),
                ('chapter', models.IntegerField()),
                ('verse', models.IntegerField()),
                ('text', models.TextField()),
            ],
        ),
        migrations.DeleteModel(
            name='Search',
        ),
    ]