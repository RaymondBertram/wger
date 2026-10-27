# This file is part of Golf Training, based on wger Workout Manager.
# SPDX-License-Identifier: AGPL-3.0-or-later

# Django
from django.conf import settings
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.utils.translation import gettext_lazy as _


class GolfPlayerProfile(models.Model):
    """Optional golf information; account details remain on the existing user."""

    class PlayingHand(models.TextChoices):
        RIGHT = 'right', _('Right')
        LEFT = 'left', _('Left')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='golf_profile',
    )
    handicap_index = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(-10), MaxValueValidator(54)],
        help_text=_('Handicap index from -10.0 to 54.0; use negative values for plus handicaps.'),
    )
    playing_hand = models.CharField(
        max_length=5,
        choices=PlayingHand.choices,
        default=PlayingHand.RIGHT,
    )
    training_goals = models.TextField(
        max_length=2000,
        blank=True,
        default='',
        validators=[MaxLengthValidator(2000)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(handicap_index__isnull=True)
                | models.Q(handicap_index__gte=-10, handicap_index__lte=54),
                name='golf_profile_handicap_range',
            ),
            models.CheckConstraint(
                condition=models.Q(playing_hand__in=['right', 'left']),
                name='golf_profile_playing_hand_valid',
            ),
        ]

    def __str__(self):
        return f'Golf profile for user {self.user_id}'

    def get_owner_object(self):
        return self
