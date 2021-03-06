'''
ARCHES - a program developed to inventory and manage immovable cultural heritage.
Copyright (C) 2013 J. Paul Getty Trust and World Monuments Fund

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import os, json, uuid
from tests import test_settings
from django.db import connection
from django.core import management
from tests.base_test import ArchesTestCase
from arches.app.models.tile import Tile
from arches.app.models import models
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpRequest
from django.core.exceptions import ObjectDoesNotExist
from arches.app.utils.betterJSONSerializer import JSONSerializer, JSONDeserializer

# these tests can be run from the command line via
# python manage.py test tests/models/tile_model_tests.py --pattern="*.py" --settings="tests.test_settings"

class TileTests(ArchesTestCase):

    @classmethod
    def setUpClass(cls):
        management.call_command('packages', operation='import_graphs', source=os.path.join(test_settings.RESOURCE_GRAPH_LOCATIONS))

        sql = """
        INSERT INTO public.resource_instances(resourceinstanceid, legacyid, graphid, createdtime)
            VALUES ('40000000-0000-0000-0000-000000000000', '40000000-0000-0000-0000-000000000000', '2f7f8e40-adbc-11e6-ac7f-14109fd34195', '1/1/2000');

        INSERT INTO node_groups(nodegroupid, legacygroupid, cardinality)
            VALUES ('99999999-0000-0000-0000-000000000001', '', 'n');

        INSERT INTO node_groups(nodegroupid, legacygroupid, cardinality)
            VALUES ('32999999-0000-0000-0000-000000000000', '', 'n');

        INSERT INTO node_groups(nodegroupid, legacygroupid, cardinality)
            VALUES ('19999999-0000-0000-0000-000000000000', '', 'n');

        INSERT INTO node_groups(nodegroupid, legacygroupid, cardinality)
            VALUES ('21111111-0000-0000-0000-000000000000', '', 'n');
        """

        cursor = connection.cursor()
        cursor.execute(sql)

    @classmethod
    def tearDownClass(cls):
        sql = """
        DELETE FROM public.node_groups
        WHERE nodegroupid = '99999999-0000-0000-0000-000000000001' OR
        nodegroupid = '32999999-0000-0000-0000-000000000000' OR
        nodegroupid = '19999999-0000-0000-0000-000000000000' OR
        nodegroupid = '21111111-0000-0000-0000-000000000000';

        DELETE FROM public.resource_instances
        WHERE resourceinstanceid = '40000000-0000-0000-0000-000000000000';

        """

        cursor = connection.cursor()
        cursor.execute(sql)

    def setUp(self):
        cursor = connection.cursor()
        cursor.execute("Truncate public.tiles Cascade;")

    def tearDown(self):
        pass

    def test_load_from_python_dict(self):
        """
        Test that we can initialize a Tile object from a Python dictionary

        """

        json = {
            "tiles": {
                "19999999-0000-0000-0000-000000000000": [{
                    "tiles": {},
                    "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
                    "parenttile_id": '',
                    "nodegroup_id": "19999999-0000-0000-0000-000000000000",
                    "tileid": "",
                    "data": {
                      "20000000-0000-0000-0000-000000000004": "TEST 1",
                      "20000000-0000-0000-0000-000000000002": "TEST 2",
                      "20000000-0000-0000-0000-000000000003": "TEST 3"
                    }
                }],
                "32999999-0000-0000-0000-000000000000": [{
                    "tiles": {},
                    "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
                    "parenttile_id": '',
                    "nodegroup_id": "32999999-0000-0000-0000-000000000000",
                    "tileid": "",
                    "data": {
                      "20000000-0000-0000-0000-000000000004": "TEST 4",
                      "20000000-0000-0000-0000-000000000002": "TEST 5",
                    }
                }]
            },
            "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
            "parenttile_id": '',
            "nodegroup_id": "20000000-0000-0000-0000-000000000001",
            "tileid": "",
            "data": {}
        }

        t = Tile(json)
        subTiles = t.tiles["19999999-0000-0000-0000-000000000000"]

        self.assertEqual(t.resourceinstance_id, "40000000-0000-0000-0000-000000000000")
        self.assertEqual(t.data, {})
        self.assertEqual(subTiles[0].data["20000000-0000-0000-0000-000000000004"], "TEST 1")


    def test_save(self):
        """
        Test that we can save a Tile object back to the database

        """
        login = self.client.login(username='admin', password='admin')

        json = {
            "tiles": {
                "72048cb3-adbc-11e6-9ccf-14109fd34195": [{
                    "tiles": {},
                    "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
                    "parenttile_id": '',
                    "nodegroup_id": "72048cb3-adbc-11e6-9ccf-14109fd34195",
                    "tileid": "",
                    "data": {
                      "72048cb3-adbc-11e6-9ccf-14109fd34195": "TEST 1"
                    }
                }]
            },
            "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
            "parenttile_id": '',
            "nodegroup_id": "7204869c-adbc-11e6-8bec-14109fd34195",
            "tileid": "",
            "data": {}
        }

        t = Tile(json)
        t.save(index=False)

        tiles = Tile.objects.filter(resourceinstance_id="40000000-0000-0000-0000-000000000000")

        self.assertEqual(tiles.count(), 2)

    def test_simple_get(self):
        """
        Test that we can get a Tile object

        """

        json = {
            "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
            "parenttile_id": '',
            "nodegroup_id": "72048cb3-adbc-11e6-9ccf-14109fd34195",
            "tileid": "",
            "data": {
              "72048cb3-adbc-11e6-9ccf-14109fd34195": "TEST 1"
            }
        }

        t = Tile(json)
        t.save(index=False)

        t2 = Tile.objects.get(tileid=t.tileid)

        self.assertEqual(t.tileid, t2.tileid)
        self.assertEqual(t2.data["72048cb3-adbc-11e6-9ccf-14109fd34195"], "TEST 1")

    def test_create_new_provisional(self):
        """
        Test that a new provisional tile is created when a user IS NOT a reviwer
        and that an authoritative tile is created when a user IS a reviwer.

        """

        self.user = User.objects.get(username='admin')

        json = {
            "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
            "parenttile_id": '',
            "nodegroup_id": "72048cb3-adbc-11e6-9ccf-14109fd34195",
            "tileid": "",
            "data": {
              "72048cb3-adbc-11e6-9ccf-14109fd34195": "AUTHORITATIVE"
            }
        }

        authoritative_tile = Tile(json)
        request = HttpRequest()
        request.user = self.user
        authoritative_tile.save(index=False, request=request)

        self.user = User.objects.create_user(username='testuser', password='TestingTesting123!')

        json = {
            "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
            "parenttile_id": '',
            "nodegroup_id": "72048cb3-adbc-11e6-9ccf-14109fd34195",
            "tileid": "",
            "data": {
              "72048cb3-adbc-11e6-9ccf-14109fd34195": "PROVISIONAL"
            }
        }

        provisional_tile = Tile(json)
        request = HttpRequest()
        request.user = self.user
        provisional_tile.save(index=False, request=request)

        self.assertEqual(provisional_tile.is_provisional(), True)
        self.assertEqual(authoritative_tile.is_provisional(), False)


    def test_save_provisional_from_athoritative(self):
        """
        Test that a provisional edit is created when a user that is not a
        reviewer edits an athoritative tile

        """

        json = {
            "tiles": {
                "72048cb3-adbc-11e6-9ccf-14109fd34195": [{
                    "tiles": {},
                    "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
                    "parenttile_id": '',
                    "nodegroup_id": "72048cb3-adbc-11e6-9ccf-14109fd34195",
                    "tileid": "",
                    "data": {
                      "72048cb3-adbc-11e6-9ccf-14109fd34195": "AUTHORITATIVE"
                    }
                }]
            },
            "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
            "parenttile_id": '',
            "nodegroup_id": "7204869c-adbc-11e6-8bec-14109fd34195",
            "tileid": "",
            "data": {}
        }

        t = Tile(json)
        t.save(index=False)
        self.user = User.objects.create_user(username='testuser', password='TestingTesting123!')
        login = self.client.login(username='testuser', password='TestingTesting123!')
        tiles = Tile.objects.filter(resourceinstance_id="40000000-0000-0000-0000-000000000000")

        provisional_tile = None
        for tile in tiles:
            if "72048cb3-adbc-11e6-9ccf-14109fd34195" in tile.data:
                provisional_tile = tile
                provisional_tile.data["72048cb3-adbc-11e6-9ccf-14109fd34195"] = 'PROVISIONAL'
        request = HttpRequest()
        request.user = self.user
        provisional_tile.save(index=False, request=request)
        tiles = Tile.objects.filter(resourceinstance_id="40000000-0000-0000-0000-000000000000")

        provisionaledits = provisional_tile.provisionaledits
        self.assertEqual(tiles.count(), 2)
        self.assertEqual(provisional_tile.data["72048cb3-adbc-11e6-9ccf-14109fd34195"], 'AUTHORITATIVE')
        self.assertEqual(provisionaledits[str(self.user.id)]['action'], 'update')
        self.assertEqual(provisionaledits[str(self.user.id)]['status'], 'review')


    def test_apply_provisional_edit(self):
        """
        Tests that provisional edit data is properly created

        """

        json = {
            "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
            "parenttile_id": '',
            "nodegroup_id": "72048cb3-adbc-11e6-9ccf-14109fd34195",
            "tileid": "",
            "data": {
              "72048cb3-adbc-11e6-9ccf-14109fd34195": "TEST 1"
            }
        }

        user = User.objects.create_user(username='testuser', password='TestingTesting123!')
        provisional_tile = Tile(json)
        request = HttpRequest()
        request.user = user
        provisional_tile.save(index=False, request=request)
        provisional_tile.apply_provisional_edit(user, {"test":"test"}, 'update')
        provisionaledits = provisional_tile.provisionaledits
        userid = str(user.id)
        self.assertEqual(provisionaledits[userid]['action'], 'update')
        self.assertEqual(provisionaledits[userid]['reviewer'], None)
        self.assertEqual(provisionaledits[userid]['value'], {"test":"test"})
        self.assertEqual(provisionaledits[userid]['status'], "review")
        self.assertEqual(provisionaledits[userid]['reviewtimestamp'], None)


    def test_user_owns_provisional(self):
        """
        Tests that a user is the owner of a provisional edit

        """

        json = {
            "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
            "parenttile_id": '',
            "nodegroup_id": "72048cb3-adbc-11e6-9ccf-14109fd34195",
            "tileid": "",
            "data": {
              "72048cb3-adbc-11e6-9ccf-14109fd34195": "TEST 1"
            }
        }

        user = User.objects.create_user(username='testuser', password='TestingTesting123!')
        provisional_tile = Tile(json)
        request = HttpRequest()
        request.user = user
        provisional_tile.save(index=False, request=request)

        self.assertEqual(provisional_tile.user_owns_provisional(user), True)

    def test_tile_deletion(self):
        """
        Tests that a tile is deleted when a user is a reviewer or owner.

        """

        json = {
            "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
            "parenttile_id": '',
            "nodegroup_id": "72048cb3-adbc-11e6-9ccf-14109fd34195",
            "tileid": "",
            "data": {
              "72048cb3-adbc-11e6-9ccf-14109fd34195": "TEST 1"
            }
        }

        owner = User.objects.create_user(username='testuser', password='TestingTesting123!')
        reviewer = User.objects.get(username='admin')

        tile1 = Tile(json)
        owner_request = HttpRequest()
        owner_request.user = owner
        tile1.save(index=False, request=owner_request)
        tile1.delete(request=owner_request)

        tile2 = Tile(json)
        reviewer_request = HttpRequest()
        reviewer_request.user = reviewer
        tile2.save(index=False, request=reviewer_request)
        tile2.delete(request=reviewer_request)

        self.assertEqual(len(Tile.objects.all()), 0)

    def test_provisional_deletion(self):
        """
        Tests that a tile is NOT deleted if a user does not have the
        privlages to delete a tile and that the proper provisionaledit is
        applied.

        """

        json = {
            "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
            "parenttile_id": '',
            "nodegroup_id": "72048cb3-adbc-11e6-9ccf-14109fd34195",
            "tileid": "",
            "data": {
              "72048cb3-adbc-11e6-9ccf-14109fd34195": "TEST 1"
            }
        }

        provisional_user = User.objects.create_user(username='testuser', password='TestingTesting123!')
        reviewer = User.objects.get(username='admin')

        tile = Tile(json)
        reviewer_request = HttpRequest()
        reviewer_request.user = reviewer
        tile.save(index=False, request=reviewer_request)

        provisional_request = HttpRequest()
        provisional_request.user = provisional_user
        tile.delete(request=provisional_request)

        self.assertEqual(len(Tile.objects.all()), 1)



        # def test_validation(self):
        #     """
        #     Test that we can get a Tile object

        #     """

        #     json = {
        #         "tiles": {},
        #         "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
        #         "parenttile_id": '',
        #         "nodegroup_id": "20000000-0000-0000-0000-000000000001",
        #         "tileid": "",
        #         "data": {
        #           "20000000-0000-0000-0000-000000000004": "TEST 1"
        #         }
        #     }

        #     t = Tile(json)
        #     self.assertTrue(t.validate()['is_valid'])

        #     json['data']['20000000-0000-0000-0000-000000000004'] = ''

        #     t2 = Tile(json)
        #     self.assertFalse(t2.validate()['is_valid'])
