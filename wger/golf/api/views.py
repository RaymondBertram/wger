# This file is part of Golf Training, based on wger Workout Manager.
# SPDX-License-Identifier: AGPL-3.0-or-later

# Django
from django.shortcuts import get_object_or_404

# Third Party
from drf_spectacular.utils import extend_schema
from rest_framework import (
    generics,
    status,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# wger
from wger.golf.api.serializers import GolfPlayerProfileSerializer
from wger.golf.models import GolfPlayerProfile


class GolfPlayerProfileView(generics.GenericAPIView):
    """Read or upsert the caller's optional profile, without accepting an owner ID."""

    serializer_class = GolfPlayerProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return GolfPlayerProfile.objects.none()
        return GolfPlayerProfile.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        profile = get_object_or_404(self.get_queryset())
        return Response(self.get_serializer(profile).data)

    def _upsert(self, request, *, partial=False):
        serializer = self.get_serializer(
            self.get_queryset().first(), data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        # The unique user relationship and update_or_create's transaction prevent
        # concurrent first writes from creating multiple profiles. Validate first
        # so an invalid request never creates an empty profile.
        profile, created = GolfPlayerProfile.objects.update_or_create(
            user=request.user, defaults=serializer.validated_data
        )
        return Response(
            self.get_serializer(profile).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(responses={200: GolfPlayerProfileSerializer, 201: GolfPlayerProfileSerializer})
    def post(self, request, *args, **kwargs):
        """Create or partially update the caller's profile."""
        return self._upsert(request, partial=True)

    @extend_schema(responses={200: GolfPlayerProfileSerializer, 201: GolfPlayerProfileSerializer})
    def put(self, request, *args, **kwargs):
        """Create or update the caller's profile."""
        return self._upsert(request)

    @extend_schema(responses={200: GolfPlayerProfileSerializer, 201: GolfPlayerProfileSerializer})
    def patch(self, request, *args, **kwargs):
        """Create or partially update the caller's profile."""
        return self._upsert(request, partial=True)
