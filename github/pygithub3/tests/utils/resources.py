#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from mock import Mock

from .base import Resource
from pygithub3.resources.base import json
from pygithub3.tests.utils.base import mock_json

json.dumps = Mock(side_effect=mock_json)
json.loads = Mock(side_effect=mock_json)


class Simple(Resource):
    pass


class HasSimple(Resource):
    _maps = {'simple': Simple}


class Nested(Resource):
    _dates = ('date', )
    _maps = {'simple': Simple, 'self_nested': 'self'}
    _collection_maps = {
        'list_collection': HasSimple,
        'items_collections': HasSimple,
        'self_nested_list': 'self',
        'self_nested_dict': 'self',
    }
