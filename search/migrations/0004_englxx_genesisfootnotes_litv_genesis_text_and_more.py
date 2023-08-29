# Generated by Django 4.2.3 on 2023-08-20 23:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0003_genesis_delete_bibleverse'),
    ]

    operations = [
        migrations.CreateModel(
            name='EngLXX',
            fields=[
                ('verseID', models.AutoField(primary_key=True, serialize=False)),
                ('canon_order', models.TextField()),
                ('book', models.TextField()),
                ('chapter', models.TextField()),
                ('startVerse', models.TextField()),
                ('endVerse', models.TextField()),
                ('verseText', models.TextField()),
            ],
            options={
                'db_table': 'englxxup',
            },
        ),
        migrations.CreateModel(
            name='GenesisFootnotes',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('footnote_id', models.TextField()),
                ('footnote_html', models.TextField()),
                ('original_footnotes_html', models.TextField()),
            ],
            options={
                'db_table': 'genesis_footnotes',
            },
        ),
        migrations.CreateModel(
            name='LITV',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('book', models.TextField()),
                ('chapter', models.TextField()),
                ('verse', models.TextField()),
                ('text', models.TextField()),
            ],
            options={
                'db_table': 'litv',
            },
        ),
        migrations.AddField(
            model_name='genesis',
            name='text',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='genesis',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]