#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from mock import Mock

from pygithub3.resources.base import Resource
from pygithub3.requests.base import Request


def mock_json(content):
    return content


def mock_response(status_code='get', content={}):
    CODES = dict(get=200, patch=200, post=201, delete=204)
    response = Mock(name='response')
    response.status_code = CODES.get(str(status_code).lower(), status_code)
    response.content = content
    return response


def mock_response_result(status_code='get'):
    response = mock_response(status_code, content=[{}, {}])
    response.headers = {'link': ''}
    return response


class DummyResource(Resource):
    pass


def loads_mock(content):
    return content
DummyResource.loads = Mock(side_effect=loads_mock)


class DummyRequest(Request):
    uri = 'dummyrequest'
    resource = DummyResource
