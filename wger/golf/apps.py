# This file is part of Golf Training, based on wger Workout Manager.
# SPDX-License-Identifier: AGPL-3.0-or-later

# Django
from django.apps import AppConfig


class GolfConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wger.golf'
    verbose_name = 'Golf Training'
