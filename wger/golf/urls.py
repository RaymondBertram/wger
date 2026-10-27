# This file is part of Golf Training, based on wger Workout Manager.
# SPDX-License-Identifier: AGPL-3.0-or-later

# Django
from django.urls import path

# wger
from wger.golf.api.views import GolfPlayerProfileView


urlpatterns = [
    path('profile/', GolfPlayerProfileView.as_view(), name='profile'),
]
