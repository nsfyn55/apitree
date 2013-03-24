import unittest
import pytest

from pyramid_apitree import (
    scan_api_tree,
    )

def make_request_methods_tuple(request_method):
    """ The Pyramid 'Configurator' 'add_view' and 'add_route' methods allow the
        'request_method' to either be a string value or a tuple of string
        values. This function duplicates that behavior. """
    if isinstance(request_method, tuple):
        return request_method
    
    if request_method is None:
        return ALL_REQUEST_METHODS
    
    return (request_method, )

class MockConfigurator(object):
    """ A mocked Pyramid configurator. """
    ALL_REQUEST_METHODS = ('GET', 'POST', 'PUT', 'DELETE', 'HEAD')
    
    def __init__(self):
        self.views = {}
        self.routes = set()
    
    def add_view(
        self,
        view,
        route_name,
        request_method=None,
        **kwargs
        ):
        request_methods = make_request_methods_tuple(request_method)
        
        view_dict = kwargs
        view_dict['view_callable'] = view
        
        for item in request_methods:
            self.views[route_name][item] = view_dict
    
    def add_route(self, name, pattern):
        assert name == pattern
        self.routes.add(pattern)

def test_empty_api_tree():
    api_tree = {}
    
    config = MockConfigurator()
    scan_api_tree(config, api_tree)
    
    assert not config.views
    assert not config.routes

class ScanAPITreeTest(unittest.TestCase):
    root_path = '/'
    
    def setUp(self):
        def dummy(*pargs, **kwargs):
            """ A dummy 'view callable' object. """
            pass
        
        self.dummy = dummy
    
    def endpoint_test(self, path, request_method=None, **expected):
        expected.setdefault('view_callable', self.dummy)
        
        request_methods = make_request_methods_tuple(request_method)
        
        config = MockConfigurator()
        scan_api_tree(config, self.api_tree, self.root_path)
        
        assert path in config.routes
        assert path in config.views
        
        for item in request_methods:
            view_dict = config.views[path][item]
            assert view_dict == expected

class TestEmptyAPITree(ScanAPITreeTest):
    def request_method_test(self, request_method):
        self.api_tree = {request_method: self.dummy}
        self.endpoint_test('/', request_method=request_method)
    
    def test_GET_endpoint(self):
        self.request_method_test('GET')
    
    def test_POST_endpoint(self):
        self.request_method_test('POST')
    
    def test_PUT_endpoint(self):
        self.request_method_test('PUT')
    
    def test_DELETE_endpoint(self):
        self.request_method_test('DELETE')
    
    def test_HEAD_endpoint(self):
        self.request_method_test('HEAD')
    
    
    
    







