""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

import unittest
import pyramid.exceptions
import pytest

from pyramid_apitree import (
    scan_api_tree,
    RequestMethod,
    GET,
    POST,
    PUT,
    DELETE,
    HEAD,
    )
from pyramid_apitree.exc import BadAPITreeError

""" An example API tree.
    
    api_tree = {
        GET: root_get,
        '/resource': {
            GET: resource_get_all,
            POST: resource_post,
            '/{resource_id}': {
                GET: resource_individual_get,
                PUT: resource_individual_update,
                DELETE: resource_individual_delete,
                '/component': {
                    GET: resource_individual_component_get,
                    }
                }
            }
        '/branch_a': endpoint_a,
        '/branch_b': (endpoint_b_get, endpoint_b_post)
        '/branch_c': {
            '': endpoint_c,
            '/branch_c_x': endpoint_c_x,
            }
        '/branch_d': {
            '': endpoint_d,
            GET: endpoint_d_get,
            }
        }
    
    """

def make_tuple(value):
    if isinstance(value, tuple):
        return value
    return (value, )

def make_request_method_tuple(value):
    """ Converts RequestMethod instances into request method strings. All
        results are tuples. """
    if isinstance(value, tuple):
        return sum(value, RequestMethod()).request_method
    return value.request_method

class MockConfigurator(object):
    """ A mocked Pyramid configurator. """
    def __init__(self):
        self.routes = {}
    
    def add_view(self, view, route_name, **kwargs):
        view_dict = kwargs.copy()
        
        if 'request_method' in view_dict:
            view_dict['request_method'] = make_tuple(
                view_dict['request_method']
                )
        
        # 'predicates_tuple' does not include 'view_callable'.
        predicates_tuple = tuple(view_dict.items())
        
        view_dict['view_callable'] = view
        view_tuple = tuple(view_dict.items())
        
        route = self.routes[route_name]
        
        if predicates_tuple in route['predicates']:
            raise pyramid.exceptions.ConfigurationError(
                "A view with this 'route_name' and predicates has already been "
                "added: {}, {}".format(route_name, predicates_tuple)
                )
        
        route['predicates'].append(predicates_tuple)
        route['views'].append(view_tuple)
    
    def add_route(self, name, pattern):
        assert name == pattern
        
        self.routes.setdefault(
            pattern,
            {'views': [], 'predicates': []}
            )

def test_empty_api_tree():
    api_tree = {}
    
    config = MockConfigurator()
    scan_api_tree(config, api_tree)
    
    assert not config.routes

class ScanTest(unittest.TestCase):
    def setUp(self):
        def target(*pargs, **kwargs):
            """ A dummy 'view_callable' object. Used as a target for tests. """
        
        def dummy(*pargs, **kwargs):
            """ Another dummy 'view_callable' object. """
        
        self.target = target
        self.dummy = dummy
    
    def endpoint_test(self, path, **expected_predicates):
        expected_dict = expected_predicates.copy()
        if 'request_method' in expected_dict:
            expected_dict['request_method'] = make_request_method_tuple(
                expected_dict['request_method']
                )
        
        expected_dict['view_callable'] = self.target
        
        expected = tuple(expected_dict.items())
        
        config = MockConfigurator()
        scan_api_tree(
            configurator=config,
            api_tree=self.api_tree,
            root_path=''
            )
        
        assert path in config.routes
        
        assert expected in config.routes[path]['views']

class TestRequestMethods(ScanTest):
    def request_method_test(self, request_method):
        self.api_tree = {request_method: self.target}
        # Use an empty string ('') for root.
        self.endpoint_test(path='', request_method=request_method)
    
    def test_GET_method(self):
        self.request_method_test(request_method=GET)
    
    def test_POST_method(self):
        self.request_method_test(request_method=POST)
    
    def test_PUT_method(self):
        self.request_method_test(request_method=PUT)
    
    def test_DELETE_method(self):
        self.request_method_test(request_method=DELETE)
    
    def test_HEAD_method(self):
        self.request_method_test(request_method=HEAD)

class TestRequestMethodsMultipleEndpoints(ScanTest):
    def test_multiple_endpoints(self):
        self.api_tree = {
            GET: self.dummy,
            POST: self.target,
            }
        self.endpoint_test(path='', request_method=POST)

class TestBranchLocationTuples(ScanTest):
    """ Branch locations can be tuples of paths and/or request methods. """
    def test_path_tuple(self):
        paths = ('/a', '/b')
        self.api_tree = {paths: self.target}
        for item in paths:
            self.endpoint_test(item)
    
    def test_request_method_tuple(self):
        methods = (GET, POST)
        self.api_tree = {methods: self.target}
        self.endpoint_test('', request_method=methods)
    
    def test_mixed_tuple(self):
        self.api_tree = {
            '/a': self.target,
            GET: self.target,
            }
        self.endpoint_test(path='/a')
        self.endpoint_test(path='', request_method=GET)
    
    def test_duplicate_paths_raises(self):
        self.api_tree = {('/', '/'): self.target,}
        with pytest.raises(pyramid.exceptions.ConfigurationError):
            self.endpoint_test('/')

@pytest.mark.a
class TestBranchObjectTuples(ScanTest):
    """ Branch objects can be tuples of views or trees. """
    def test_view_tuple_duplicate_predicates_raises(self):
        """ If a branch object is a tuple of views, those views must have
            distinct predicates. """
        self.api_tree = {'/': (self.target, self.dummy)}
        with pytest.raises(pyramid.exceptions.ConfigurationError):
            self.endpoint_test('/')
    
    @pytest.mark.b
    def test_view_tuple(self):
        self.dummy.view_kwargs = {'predicate': 'value'}
        self.api_tree = {'/': (self.target, self.dummy)}
        self.endpoint_test('/')
    
    def test_tree_tuple(self):
        self.api_tree = {
            '/a': (
                {'/x': self.target},
                {'/y': self.target},
                )
            }
        for path in ['/a/x', '/a/y']:
            self.endpoint_test(path)
    
    def test_mixed_tuple(self):
        self.api_tree = {
            '/x': (
                {'/y': self.target},
                self.target,
                )
            }
        for path in ['/x', '/x/y']:
            self.endpoint_test(path)

class TestBranch(ScanTest):
    def test_branch_no_request_method(self):
        self.api_tree = {'/resource': self.target}
        self.endpoint_test('/resource')
    
    def test_branch_yes_request_method(self):
        self.api_tree = {
            '/resource': {
                GET: self.target,
                }
            }
        self.endpoint_test('/resource', request_method=GET)
    
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
                    GET: self.target
                    }
                }
            }
        self.endpoint_test('/resource/component', request_method=GET)
    
    def test_branch_multiple_branches(self):
        self.api_tree = {
            '/resource': {
                '/other_component': self.dummy,
                '/component': self.target,
                }
            }
        self.endpoint_test('/resource/component')

class TestViewKwargs(ScanTest):
    def test_view_kwargs(self):
        self.target.view_kwargs = {'predicate': 'predicate value'}
        self.api_tree = {
            '': self.target,
            }
        self.endpoint_test('', **self.target.view_kwargs)
    
    def test_route_request_method_overrides_view_kwargs(self):
        """ When the API tree branch route is a request method keyword AND a
            'request_method' value is included in the 'view_kwargs' dict, the
            API tree should override 'view_kwargs'. """
        self.target.view_kwargs = {'request_method': POST}
        self.api_tree = {
            GET: self.target,
            }
        self.endpoint_test('', request_method=GET)

class TestExceptions(unittest.TestCase):
    """ Confirm that appropriate errors are raised in expected situations. """
    def setUp(self):
        def dummy(*pargs, **kwargs):
            """ A dummy view callable. """
        self.dummy = dummy
    
    def exception_test(self, api_tree):
        configurator = MockConfigurator()
        with pytest.raises(BadAPITreeError):
            scan_api_tree(configurator, api_tree)
    
    def test_request_method_route_gets_dictionary(self):
        """ When a request-method-specific-route (i.e. '/GET') is assigned a
            dictionary value in the API tree, an error should be raised.
            
            This is because it is impossible to build upon a request-method-
            specific route; the request method does not form a part of the URL.
            """
        api_tree = {
            GET: {
                '/xxx': self.dummy
                }
            }
        self.exception_test(api_tree)
    
    def test_invalid_branch_route_object(self):
        """ A 'branch route' is something besides a string, a request method
            string, or a tuple of request methods. """
        api_tree = {object(): self.dummy}
        self.exception_test(api_tree)
    
    







