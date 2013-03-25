import unittest
import pytest

from pyramid_apitree import (
    scan_api_tree,
    )

""" An example API tree.
    
    api_tree = {
        'GET': root_get,
        '/resource': {
            'GET': resource_get_all,
            'POST': resource_post,
            '.{resource_id}': {
                'GET': resource_individual_get,
                'PUT': resource_individual_update,
                'DELETE': resource_individual_delete,
                '/component': {
                    'GET': resource_individual_component_get,
                    }
                }
            }
        }
    
    """

def make_request_methods_tuple(request_method):
    """ The Pyramid 'Configurator' 'add_view' and 'add_route' methods allow the
        'request_method' to either be a string value or a tuple of string
        values. This function duplicates that behavior. """
    ALL_REQUEST_METHODS = ('GET', 'POST', 'PUT', 'DELETE', 'HEAD')
    
    if isinstance(request_method, tuple):
        return request_method
    
    if request_method is None:
        return ALL_REQUEST_METHODS
    
    return (request_method, )

class MockConfigurator(object):
    """ A mocked Pyramid configurator. """
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

class ScanTest(unittest.TestCase):
    def target(*pargs, **kwargs):
        """ A dummy 'view_callable' object. Used as a target for tests. """
    
    def dummy(*pargs, **kwargs):
        """ Another dummy 'view_callable' object. """
    
    def endpoint_test(self, path, request_method=None, expected={}):
        expected['view_callable'] = self.target
        
        request_methods = make_request_methods_tuple(request_method)
        
        config = MockConfigurator()
        scan_api_tree(
            configurator=config,
            api_tree=self.api_tree,
            root_path='')
        
        assert path in config.routes
        assert path in config.views
        
        for item in request_methods:
            view_dict = config.views[path][item]
            assert view_dict == expected

class TestRequestMethods(ScanTest):
    def request_method_test(self, request_method=None):
        self.api_tree = {request_method: self.target}
        # Use an empty string ('') for root.
        self.endpoint_test(path='', request_method=request_method)
    
    def test_no_request_method(self):
        self.request_method_test()
    
    def test_yes_request_method(self):
        self.request_method_test(request_method='GET')
    
    def test_multiple_request_methods(self):
        self.request_method_test(request_method=('GET', 'POST'))

class TestRequestMethodsMultipleEndpoints(ScanTest):
    def test_multiple_endpoints(self):
        self.api_tree = {
            'GET': self.dummy,
            'POST': self.target,
            }
        self.endpoint_test(path='', request_method='POST')

class TestBranch(ScanTest):
    def test_branch(self):
        self.api_tree = {'/resource': self.target}
        self.endpoint_test('/resource')
    
    def test_branch_request_method(self):
        self.api_tree = {
            '/resource': {
                'GET': self.target,
                }
            }
        self.endpoint_test('/resource', 'GET')
    
    def test_multiple_branches(self):
        self.api_tree = {
            '/other_resource': self.dummy,
            '/resource': self.target,
            }
        self.endpoint_test('/resource')

class TestComplexBranch(ScanTest):
    def test_branch_branch(self):
        self.api_tree = {
            '/resource': {
                '/component': self.target
                }
            }
        self.endpoint_test('/resource/component')
    
    def test_branch_branch_request_method(self):
        self.api_tree = {
            '/resource': {
                '/component': {
                    'GET': self.target
                    }
                }
            }
        self.endpoint_test('/resource/component', request_method='GET')
    
    def test_branch_multiple_branches(self):
        self.api_tree = {
            '/resource': {
                '/other_component': self.dummy,
                '/component': self.target,
                }
            }
        self.endpoint_test('/resource/component')

class TestViewKwargs(ScanTest):
    def target(*pargs, **kwargs):
        """ A view callable with a 'view_kwargs' attribute. The API tree scan
            should automatically unpack the 'view_kwargs' when calling
            'configurator.add_view()'. """
    
    target.view_kwargs = {'predicate': 'predicate value'}
    
    def test_view_kwargs(self):
        self.api_tree = {
            '': self.target,
            }
        self.endpoint_test('', expected=self.target.view_kwargs)
    
    







