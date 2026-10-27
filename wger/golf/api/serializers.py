# This file is part of Golf Training, based on wger Workout Manager.
# SPDX-License-Identifier: AGPL-3.0-or-later

# Third Party
from rest_framework import serializers

# wger
from wger.golf.models import GolfPlayerProfile


class GolfPlayerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GolfPlayerProfile
        fields = (
            'id',
            'user',
            'handicap_index',
            'playing_hand',
            'training_goals',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
