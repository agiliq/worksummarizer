#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from .base import Resource

__all__ = ('Org', )


class Org(Resource):

    _dates = ('created_at', )

    def __str__(self):
        return '<Org (%s)>' % getattr(self, 'name', '')
