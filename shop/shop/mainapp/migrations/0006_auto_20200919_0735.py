# Generated by Django 3.1.1 on 2020-09-19 07:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0005_auto_20200919_0622'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smartphone',
            name='sd',
            field=models.BooleanField(default=True, verbose_name='Cart exists?'),
        ),
        migrations.AlterField(
            model_name='smartphone',
            name='sd_volume',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Max capacity of sd'),
        ),
    ]