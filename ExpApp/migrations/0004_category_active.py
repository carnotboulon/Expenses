# Generated by Django 2.0.3 on 2018-04-01 17:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ExpApp', '0003_auto_20170111_2358'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='active',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]
