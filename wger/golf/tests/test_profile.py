# This file is part of Golf Training, based on wger Workout Manager.
# SPDX-License-Identifier: AGPL-3.0-or-later

# Standard Library
from datetime import timedelta
from decimal import Decimal

# Django
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import (
    IntegrityError,
    transaction,
)
from django.urls import reverse

# Third Party
from rest_framework.test import APIClient

# wger
from wger.core.tests.base_testcase import WgerTestCase
from wger.golf.models import GolfPlayerProfile


class GolfPlayerProfileModelTestCase(WgerTestCase):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.get(username='test')

    def test_profile_defaults_and_relationship(self):
        profile = GolfPlayerProfile.objects.create(user=self.user)

        self.assertIsNone(profile.handicap_index)
        self.assertEqual(profile.playing_hand, GolfPlayerProfile.PlayingHand.RIGHT)
        self.assertEqual(profile.training_goals, '')
        self.assertEqual(self.user.golf_profile, profile)
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)
        self.assertEqual(profile.get_owner_object(), profile)
        profile.full_clean()

    def test_one_profile_per_user(self):
        GolfPlayerProfile.objects.create(user=self.user)
        with self.assertRaises(IntegrityError), transaction.atomic():
            GolfPlayerProfile.objects.create(user=self.user)

    def test_handicap_model_validation(self):
        profile = GolfPlayerProfile(user=self.user)
        for value in (None, Decimal('-10.0'), Decimal('0.0'), Decimal('54.0')):
            with self.subTest(valid=value):
                profile.handicap_index = value
                profile.full_clean()
        for value in (Decimal('-10.1'), Decimal('54.1'), Decimal('12.34')):
            with self.subTest(invalid=value):
                profile.handicap_index = value
                with self.assertRaises(ValidationError):
                    profile.full_clean()

    def test_playing_hand_and_goals_model_validation(self):
        for fields in ({'playing_hand': 'both'}, {'training_goals': 'x' * 2001}):
            with self.subTest(fields=fields):
                profile = GolfPlayerProfile(user=self.user, **fields)
                with self.assertRaises(ValidationError):
                    profile.full_clean()

    def test_database_constraints(self):
        for fields in (
            {'handicap_index': Decimal('-10.1')},
            {'handicap_index': Decimal('54.1')},
            {'playing_hand': 'both'},
        ):
            with self.subTest(fields=fields):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    GolfPlayerProfile.objects.create(user=self.user, **fields)


class GolfPlayerProfileApiTestCase(WgerTestCase):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.get(username='test')
        self.other_user = get_user_model().objects.get(username='admin')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = reverse('golf:profile')

    def test_missing_profile_returns_404_without_creating(self):
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertFalse(GolfPlayerProfile.objects.filter(user=self.user).exists())

    def test_create_and_retrieve(self):
        payload = {
            'handicap_index': '18.4',
            'playing_hand': 'left',
            'training_goals': 'Improve putting',
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 201)
        profile = GolfPlayerProfile.objects.get(user=self.user)
        self.assertEqual(profile.handicap_index, Decimal('18.4'))
        self.assertEqual(profile.playing_hand, 'left')
        self.assertEqual(profile.training_goals, payload['training_goals'])
        self.assertEqual(response.data['user'], self.user.pk)
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)
        retrieved = self.client.get(self.url)
        self.assertEqual(retrieved.status_code, 200)
        self.assertEqual(retrieved.data, response.data)

    def test_all_write_methods_can_create_and_update(self):
        for method in ('post', 'put', 'patch'):
            with self.subTest(method=method):
                # Each method must work for an existing account with no golf profile.
                GolfPlayerProfile.objects.filter(user=self.user).delete()
                request = getattr(self.client, method)
                created = request(self.url, {'playing_hand': 'left'}, format='json')
                self.assertEqual(created.status_code, 201)
                updated = request(self.url, {'training_goals': 'Practice daily'}, format='json')
                self.assertEqual(updated.status_code, 200)
                self.assertEqual(updated.data['id'], created.data['id'])
                self.assertEqual(updated.data['training_goals'], 'Practice daily')
                self.assertEqual(GolfPlayerProfile.objects.filter(user=self.user).count(), 1)

    def test_patch_preserves_unsent_fields_and_updates_timestamp(self):
        profile = GolfPlayerProfile.objects.create(
            user=self.user, playing_hand='left', handicap_index=Decimal('12.3')
        )
        created_at = profile.created_at
        updated_at = profile.updated_at - timedelta(days=1)
        GolfPlayerProfile.objects.filter(pk=profile.pk).update(updated_at=updated_at)
        response = self.client.patch(self.url, {'training_goals': 'More practice'}, format='json')
        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.playing_hand, 'left')
        self.assertEqual(profile.handicap_index, Decimal('12.3'))
        self.assertEqual(profile.created_at, created_at)
        self.assertGreater(profile.updated_at, updated_at)

    def test_handicap_boundaries_and_clear(self):
        for value in ('-10.0', '0.0', '54.0', None):
            with self.subTest(value=value):
                response = self.client.patch(self.url, {'handicap_index': value}, format='json')
                self.assertIn(response.status_code, (200, 201))
                profile = GolfPlayerProfile.objects.get(user=self.user)
                self.assertEqual(profile.handicap_index, None if value is None else Decimal(value))

    def test_invalid_handicap_does_not_create_profile(self):
        for value in ('-10.1', '54.1', '12.34', 'abc', 'NaN', 'Infinity'):
            with self.subTest(value=value):
                response = self.client.post(self.url, {'handicap_index': value}, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertIn('handicap_index', response.data)
                self.assertFalse(GolfPlayerProfile.objects.filter(user=self.user).exists())

    def test_invalid_update_leaves_profile_unchanged(self):
        profile = GolfPlayerProfile.objects.create(user=self.user, handicap_index=Decimal('12.3'))
        response = self.client.patch(self.url, {'handicap_index': '54.1'}, format='json')
        self.assertEqual(response.status_code, 400)
        profile.refresh_from_db()
        self.assertEqual(profile.handicap_index, Decimal('12.3'))

    def test_invalid_hand_and_goals(self):
        for payload in (
            {'playing_hand': 'both'},
            {'playing_hand': ''},
            {'playing_hand': None},
            {'training_goals': 'x' * 2001},
            {'training_goals': None},
        ):
            with self.subTest(payload=payload):
                response = self.client.post(self.url, payload, format='json')
                self.assertEqual(response.status_code, 400)
        self.assertFalse(GolfPlayerProfile.objects.filter(user=self.user).exists())

    def test_empty_optional_fields(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data['handicap_index'])
        self.assertEqual(response.data['training_goals'], '')

    def test_authentication_required_for_every_method(self):
        self.client.force_authenticate(user=None)
        for method in ('get', 'post', 'put', 'patch'):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(response.status_code, 403)
        self.assertFalse(GolfPlayerProfile.objects.exists())

    def test_session_writes_require_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.url, {}, format='json').status_code, 403)
        self.assertFalse(GolfPlayerProfile.objects.filter(user=self.user).exists())

    def test_owner_and_server_fields_cannot_be_overridden(self):
        other = GolfPlayerProfile.objects.create(user=self.other_user, training_goals='Private')
        payload = {
            'id': other.pk,
            'user': self.other_user.pk,
            'training_goals': 'Mine',
            'created_at': '2000-01-01T00:00:00Z',
            'updated_at': '2000-01-01T00:00:00Z',
        }
        for method in ('post', 'put', 'patch'):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url, payload, format='json')
                self.assertIn(response.status_code, (200, 201))
                self.assertEqual(response.data['user'], self.user.pk)
                self.assertNotEqual(response.data['id'], other.pk)
                self.assertNotEqual(response.data['created_at'], payload['created_at'])
                self.assertNotEqual(response.data['updated_at'], payload['updated_at'])
        other.refresh_from_db()
        self.assertEqual(other.training_goals, 'Private')

    def test_get_is_scoped_to_authenticated_user(self):
        mine = GolfPlayerProfile.objects.create(user=self.user, training_goals='Mine')
        other = GolfPlayerProfile.objects.create(user=self.other_user, training_goals='Private')
        response = self.client.get(self.url, {'user': self.other_user.pk})
        self.assertEqual(response.data['id'], mine.pk)
        self.client.force_authenticate(self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.data['id'], other.pk)
        self.assertEqual(response.data['training_goals'], 'Private')

    def test_no_list_detail_or_delete_endpoints(self):
        profile = GolfPlayerProfile.objects.create(user=self.other_user)
        self.assertEqual(self.client.get(f'{self.url}{profile.pk}/').status_code, 404)
        self.assertEqual(self.client.get('/api/v2/golf/').status_code, 404)
        self.assertEqual(self.client.delete(self.url).status_code, 405)
        self.assertTrue(GolfPlayerProfile.objects.filter(pk=profile.pk).exists())

    def test_malformed_payload(self):
        self.assertEqual(self.client.post(self.url, [], format='json').status_code, 400)
