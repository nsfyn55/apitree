import unittest
import pytest

from pyramid_apitree import (
    scan_api_tree,
    )

class MockConfigurator(object):
    """ A mocked Pyramid configurator. """
    def __init__(self):
        self.endpoints = {}
    
    def get_endpoint(self, route_name):
        return self.endpoints.setdefault(route_name, dict())
    
    def add_view(self, view_callable, route_name, **kwargs):
        endpoint = self.get_endpoint(route_name)
        endpoint['view_callable'] = view_callable
        endpoint.update(kwargs)
    
    def add_route(self, name, pattern):
        endpoint = self.get_endpoint(name)
        endpoint['pattern'] = pattern

class TestScanAPITree(unittest.TestCase):
    def scan_test(self, route_name, **expected):
        config = MockConfigurator()
        scan_api_tree(config, self.api_tree)
        
        assert route_name in config.endpoints
        endpoint = config.endpoints[route_name]
        
        assert endpoint == expected







