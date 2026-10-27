# This file is part of Golf Training, based on wger Workout Manager.
# SPDX-License-Identifier: AGPL-3.0-or-later

# Django
import django.db.models.deletion
from django.conf import settings
from django.core import validators
from django.db import (
    migrations,
    models,
)


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name='GolfPlayerProfile',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'handicap_index',
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        help_text=(
                            'Handicap index from -10.0 to 54.0; '
                            'use negative values for plus handicaps.'
                        ),
                        max_digits=3,
                        null=True,
                        validators=[
                            validators.MinValueValidator(-10),
                            validators.MaxValueValidator(54),
                        ],
                    ),
                ),
                (
                    'playing_hand',
                    models.CharField(
                        choices=[('right', 'Right'), ('left', 'Left')],
                        default='right',
                        max_length=5,
                    ),
                ),
                (
                    'training_goals',
                    models.TextField(
                        blank=True,
                        default='',
                        max_length=2000,
                        validators=[validators.MaxLengthValidator(2000)],
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'user',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='golf_profile',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'constraints': [
                    models.CheckConstraint(
                        condition=models.Q(handicap_index__isnull=True)
                        | models.Q(handicap_index__gte=-10, handicap_index__lte=54),
                        name='golf_profile_handicap_range',
                    ),
                    models.CheckConstraint(
                        condition=models.Q(playing_hand__in=['right', 'left']),
                        name='golf_profile_playing_hand_valid',
                    ),
                ],
            },
        ),
    ]
