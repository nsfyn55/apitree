""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

import unittest
import pyramid.exceptions
import pytest
from contextlib import contextmanager
from copy import deepcopy

from pyramid_apitree import (
    scan_api_tree,
    add_catchall,
    RequestMethod,
    GET,
    POST,
    PUT,
    DELETE,
    HEAD,
    )
import pyramid_apitree.tree_scan
from pyramid_apitree.exc import APITreeError
from pyramid_apitree.util import is_container

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

def make_set(value):
    if isinstance(value, tuple):
        return set(value)
    return set((value, ))

def make_request_method_set(value):
    """ Converts RequestMethod instances into request method strings. All
        results are tuples. """
    if isinstance(value, tuple):
        return set(sum(value, RequestMethod()).request_method)
    return set(value.request_method)

class MockConfigurator(object):
    """ A mocked Pyramid configurator. """
    def __init__(self):
        self.routes = {}
    
    def add_view(self, view, route_name, **kwargs):
        view_dict = kwargs.copy()
        
        if 'request_method' in view_dict:
            view_dict['request_method'] = make_set(
                view_dict['request_method']
                )
        
        # 'predicates_dict' does not include 'view'.
        predicates_dict = deepcopy(view_dict)
        
        view_dict['view'] = view
        
        route = self.routes[route_name]
        
        if predicates_dict in route['predicates']:
            raise pyramid.exceptions.ConfigurationError(
                "A view with this 'route_name' and predicates has already been "
                "added: {}, {}".format(route_name, predicates_dict)
                )
        
        route['predicates'].append(predicates_dict)
        route['views'].append(view_dict)
    
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

class TestExceptions(unittest.TestCase):
    """ Confirm that appropriate errors are raised in expected situations. """
    def setUp(self):
        def dummy(*pargs, **kwargs):
            """ A dummy view callable. """
        self.dummy = dummy
    
    def exception_test(self, api_tree):
        configurator = MockConfigurator()
        with pytest.raises(APITreeError):
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

class ScanTest(unittest.TestCase):
    def setUp(self):
        def target(*pargs, **kwargs):
            """ A dummy 'view callable'  object. Used as a target for tests. """
        
        def dummy(*pargs, **kwargs):
            """ Another dummy 'view callable' object. """
        
        self.target = target
        self.dummy = dummy
    
    def do_scan(self):
        self.config = MockConfigurator()
        scan_api_tree(
            configurator=self.config,
            api_tree=self.api_tree,
            root_path=''
            )
    
    def prepare_endpoint_test(self, paths, do_scan=True, **expected_predicates):
        if not is_container(paths, (list, tuple)):
            paths = tuple([paths])
        
        expected_dict = expected_predicates.copy()
        if 'request_method' in expected_dict:
            expected_dict['request_method'] = make_request_method_set(
                expected_dict['request_method']
                )
        
        expected_dict['view'] = self.target
        
        if do_scan:
            self.do_scan()
        
        for path in paths:
            assert path in self.config.routes
        
        return paths, expected_dict
    
    def endpoint_test(self, *pargs, **kwargs):
        paths, expected = self.prepare_endpoint_test(*pargs, **kwargs)
        for path in paths:
            assert expected in self.config.routes[path]['views']
    
    def endpoint_missing_test(self, *pargs, **kwargs):
        paths, expected = self.prepare_endpoint_test(*pargs, **kwargs)
        
        for path in paths:
            assert expected not in self.config.routes[path]['views']

class TestRequestMethods(ScanTest):
    def request_method_test(self, request_method):
        self.api_tree = {request_method: self.target}
        # Use an empty string ('') for root.
        self.endpoint_test('', request_method=request_method)
    
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
        self.endpoint_test('', request_method=POST)

class TestBranchLocationTuples(ScanTest):
    """ Branch locations can be tuples of paths and/or request methods. """
    def test_path_tuple(self):
        paths = ('/a', '/b')
        self.api_tree = {paths: self.target}
        self.endpoint_test(paths)
    
    def test_request_method_tuple(self):
        methods = (GET, POST)
        self.api_tree = {methods: self.target}
        self.endpoint_test('', request_method=methods)
    
    def test_mixed_tuple(self):
        self.api_tree = {
            '/a': self.target,
            GET: self.target,
            }
        self.endpoint_test('/a')
        self.endpoint_test('', request_method=GET)
    
    def test_duplicate_paths_raises(self):
        self.api_tree = {('/', '/'): self.target,}
        with pytest.raises(pyramid.exceptions.ConfigurationError):
            self.endpoint_test('/')

class TestBranchObjectTuples(ScanTest):
    """ Branch objects can be tuples of views or trees. """
    def test_view_tuple_duplicate_predicates_raises(self):
        """ If a branch object is a tuple of views, those views must have
            distinct predicates. """
        self.api_tree = {'/': (self.target, self.dummy)}
        with pytest.raises(pyramid.exceptions.ConfigurationError):
            self.endpoint_test('/')
    
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
        self.endpoint_test(['/a/x', '/a/y'])
    
    def test_mixed_tuple(self):
        self.api_tree = {
            '/x': (
                {'/y': self.target},
                self.target,
                )
            }
        self.endpoint_test(['/x', '/x/y'])

class TestTreeListOfTuples(ScanTest):
    """ An API tree can be a list of 2-tuples. """
    def test_tree_list_of_tuples(self):
        self.api_tree = [('/', self.target)]
        self.endpoint_test('/')
    
    def test_branch_list_of_tuples(self):
        self.api_tree = {
            '/a': [('/b', self.target)]
            }
        self.endpoint_test('/a/b')
    
    def test_order_preserved_before(self):
        """ Using the 'list of 2-tuples' style preserves the order in which
            views are added to the Pyramid configurator. """
        # Distinct predicate values.
        self.target.view_kwargs = {'a': 'b'}
        
        self.api_tree = [
            ('/', self.target),
            ('/', self.dummy),
            ]
        self.do_scan()
        
        views = [
            dict(item)['view']
            for item in self.config.routes['/']['views']
            ]
        assert views == [self.target, self.dummy]

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

class AddCatchallTest(ScanTest):
    """ Test 'add_catchall' function. """
    
    class DummyViewCallable(object):
        """ Base class for dummy view callables. """
        def __init__(self, **predicates):
            self.view_kwargs = predicates
        
        def __call__(self, *pargs, **kwargs):
            pass
    
    class DummyViewCallableA(DummyViewCallable):
        pass
    
    class DummyViewCallableB(DummyViewCallableA):
        pass
    
    class DummyViewCallableC(DummyViewCallableA):
        pass
    
    class DummyViewCallableQ(DummyViewCallable):
        pass
    
    def setUp(self):
        """ The 'catchall' view callable (in this case, 'target') must have
            distinct predicates to avoid raising a
            pyramid.exceptions.ConfigurationError. """
        super().setUp()
        self.target.view_kwargs = {}
        self.dummy.view_kwargs = {}
    
    def prepare_endpoint_test(self, *pargs, **kwargs):
        """ Prevent premature API tree scan. """
        return super().prepare_endpoint_test(do_scan=False, *pargs, **kwargs)
    
    def add_target_catchall(self, **kwargs):
        add_catchall(
            configurator=self.config,
            api_tree=self.api_tree,
            catchall=self.target,
            **kwargs
            )
    
    def prepare_catchall(self, **kwargs):
        self.do_scan()
        self.add_target_catchall(**kwargs)
    
    def prepare_endpoint_expected(self, **kwargs):
        expected = {}
        if hasattr(self.target, 'catchall_custom_predicate'):
            expected['custom_predicates'] = (
                self.target.catchall_custom_predicate,
                )
        expected.update(kwargs)
        return expected
    
    def catchall_endpoint_test(self, paths, **kwargs):
        expected = self.prepare_endpoint_expected(**kwargs)
        self.endpoint_test(paths, **expected)
    
    def catchall_endpoint_missing_test(self, paths, **kwargs):
        expected = self.prepare_endpoint_expected(**kwargs)
        self.endpoint_missing_test(paths, **expected)
    
    def catchall_test(self, paths, **kwargs):
        self.prepare_catchall()
        self.catchall_endpoint_test(paths, **kwargs)

class TestAddCatchallPasses(AddCatchallTest):
    """ Test 'add_catchall' passes in expected situations. """
    
    def test_duplicate_predicates_passes(self):
        """ By default, 'add_catchall' adds a custom predicate to the 'catchall'
            view callable. This custom predicate allows the catchall to be added
            to any route; if predicate checks for all other views at that route
            fail, the 'catchall' view callable will be called. """
        assert self.target.view_kwargs == self.dummy.view_kwargs
        self.api_tree = {'/': self.dummy}
        self.do_scan()
        self.add_target_catchall()
    
    def test_missing_view_kwargs_passes(self):
        """ 'add_catchall' passes when the catchall has no 'view_kwargs'
            attribute. """
        del self.target.view_kwargs
        self.api_tree = {'/': self.DummyViewCallableA()}
        self.do_scan()
        self.add_target_catchall()

class TestAddCatchallPredicateSources(AddCatchallTest):
    """ Sources for 'predicate' 'view_kwargs' values. """
    
    # ----------------------- Generic predicates -----------------------
    
    @contextmanager
    def predicates_test_context(self):
        expected = {'x': 'y'}
        self.api_tree = {'/': self.dummy}
        yield expected
        self.catchall_endpoint_test('/', **expected)
    
    def test_predicates_from_catchall_view_kwargs(self):
        with self.predicates_test_context() as expected:
            self.target.view_kwargs = expected.copy()
            self.prepare_catchall()
    
    def test_predicates_from_view_kwargs(self):
        with self.predicates_test_context() as expected:
            self.prepare_catchall(view_kwargs=expected)
    
    def test_predicates_from_additional_view_kwargs(self):
        with self.predicates_test_context() as expected:
            self.prepare_catchall(additional_view_kwargs=expected)
    
    def test_view_kwargs_replaces_catchall_view_kwargs(self):
        with self.predicates_test_context() as expected:
            self.target.view_kwargs = {'a': 'b'}
            self.prepare_catchall(view_kwargs=expected)
    
    def test_additional_view_kwargs_updates_catchall_view_kwargs(self):
        self.api_tree = {'/': self.dummy}
        self.target.view_kwargs = {'a': 'b', 'c': 'd'}
        self.prepare_catchall(additional_view_kwargs={'c': 'm', 'x': 'y'})
        self.catchall_endpoint_test('/', **{'a': 'b', 'c': 'm', 'x': 'y'})
    
    def test_additional_view_kwargs_updates_view_kwargs(self):
        self.api_tree = {'/': self.dummy}
        self.prepare_catchall(
            view_kwargs = {'a': 'b', 'c': 'd'},
            additional_view_kwargs={'c': 'm', 'x': 'y'},
            )
        self.catchall_endpoint_test('/', **{'a': 'b', 'c': 'm', 'x': 'y'})
    
    # --------------- 'request_method' predicate sources ---------------
    
    def test_request_method_copied_from_api_tree(self):
        """ Catchall copies the request method when the request method is
            specified in the API tree.
            
            This test also confirms that catchall 'view_kwargs' values
            compliment 'request_method' value from subject views. """
        self.api_tree = {GET: self.dummy}
        self.catchall_test('', request_method=GET)
    
    def test_request_method_multiple_copied_from_api_tree(self):
        self.api_tree = {
            GET: self.DummyViewCallableA(),
            POST: self.DummyViewCallableA(),
            }
        self.catchall_test('', request_method=(GET, POST))
    
    def test_request_method_copied_from_subject_view_kwargs(self):
        """ Catchall copies 'request_method' when the request method is
            specified in 'view_kwargs' of view callable to which catchall is
            applied. """
        self.dummy.view_kwargs['request_method'] = 'GET'
        self.api_tree = {'/': self.dummy}
        self.catchall_test('/', request_method=GET)
    
    # ------------------- Predicate sources priority -------------------
    
    @contextmanager
    def overrides_request_method_test_context(self):
        self.api_tree = {POST: self.dummy}
        yield
        self.catchall_endpoint_test('', **{'request_method': GET})
    
    @contextmanager
    def compliments_request_method_test_context(self):
        self.api_tree = {POST: self.dummy}
        yield
        self.catchall_endpoint_test('', **{'x': 'y', 'request_method': POST})
    
    def test_catchall_view_kwargs_overrides_request_method(self):
        """ When catchall 'view_kwargs' specifies 'request_method', it overrides
            'request_method' from subject view. """
        with self.overrides_request_method_test_context():
            self.target.view_kwargs.update({'request_method': 'GET'})
            self.prepare_catchall()
    
    def test_catchall_view_kwargs_compliments_request_method(self):
        """ When catchall 'view_kwargs' does not specify 'request_method',
            'request_method' from subject view is used. """
        with self.compliments_request_method_test_context():
            self.target.view_kwargs.update({'x': 'y'})
            self.prepare_catchall()
    
    def test_view_kwargs_overrides_request_method(self):
        """ When 'add_catchall' 'view_kwargs' argument specifies
            'request_method', it overrides 'request_method' from subject
            view. """
        with self.overrides_request_method_test_context():
            self.prepare_catchall(view_kwargs={'request_method': 'GET'})
    
    def test_view_kwargs_compliments_request_method(self):
        """ When 'add_catchall' 'view_kwargs' argument does not specify
            'request_method', 'request_method' from subject view is used. """
        with self.compliments_request_method_test_context():
            self.prepare_catchall(view_kwargs={'x': 'y'})
    
    @contextmanager
    def overrides_custom_predicates_test_context(self):
        self.api_tree = {'/': self.dummy}
        yield
        self.catchall_endpoint_test('/', **{'custom_predicates': 'xxx'})
    
    @contextmanager
    def compliments_custom_predicates_test_context(self):
        self.api_tree = {'/': self.dummy}
        yield
        self.catchall_endpoint_test('/', **{
            'x': 'y',
            'custom_predicates': (
                self.target.catchall_custom_predicate,
                )
            })
    
    def test_catchall_view_kwargs_overrides_custom_predicates(self):
        with self.overrides_custom_predicates_test_context():
            self.target.view_kwargs.update({'custom_predicates': 'xxx'})
            self.prepare_catchall()
    
    def test_catchall_view_kwargs_compliments_custom_predicates(self):
        with self.compliments_custom_predicates_test_context():
            self.target.view_kwargs.update({'x': 'y'})
            self.prepare_catchall()
    
    def test_view_kwargs_overrides_custom_predicates(self):
        with self.overrides_custom_predicates_test_context():
            self.prepare_catchall(view_kwargs={'custom_predicates': 'xxx'})
    
    def test_view_kwargs_compliments_custom_predicates(self):
        with self.compliments_custom_predicates_test_context():
            self.prepare_catchall(view_kwargs={'x': 'y'})

class TestAddCatchallRoutes(AddCatchallTest):
    """ 'add_catchall' works with various route configurations. """
    
    # ---------------- Catchall added to subject views -----------------
    
    def test_single_view(self):
        """ Path with single view callable. """
        self.api_tree = {'/': self.dummy}
        self.catchall_test('/')
    
    def test_multiple_views(self):
        """ Path with multiple view callables. """
        self.api_tree = {
            '/': (
                self.DummyViewCallableA(a='a'),
                self.DummyViewCallableB(b='b'),
                )
            }
        self.catchall_test('/')
    
    def test_multiple_routes(self):
        """ Multiple paths. """
        self.api_tree = {
            '/a': self.DummyViewCallableA(),
            '/b': self.DummyViewCallableB(),
            }
        self.catchall_test(['/a', '/b'])
    
    def test_single_route_multiple_catchalls(self):
        """ When multiple catchalls are added to a single route, they do not
            raise a ConfigurationError. """
        self.api_tree = {'/': self.dummy}
        self.do_scan()
        for item in [self.DummyViewCallable() for i in range(2)]:
            add_catchall(
                configurator=self.config,
                api_tree=self.api_tree,
                catchall=item,
                )
            self.target = item
            self.catchall_endpoint_test('/')

class TestAddCatchallTypeTargeting(AddCatchallTest):
    """ 'add_catchall' only applies to views of specified types. """
    
    def test_specific_type(self):
        """ Add catchall only to views of a specific type. """
        self.api_tree = {
            '/a': self.DummyViewCallableA(),
            '/b': self.DummyViewCallableB(),
            }
        
        self.prepare_catchall(target_classinfo=self.DummyViewCallableB)
        self.catchall_endpoint_test('/b')
        self.catchall_endpoint_missing_test('/a')
    
    def test_parent_type(self):
        """ Add catchall to all views descended from a specific type. """
        self.api_tree = {
            '/a': self.DummyViewCallableA(),
            '/b': self.DummyViewCallableB(),
            '/q': self.DummyViewCallableQ(),
            }
        self.prepare_catchall(target_classinfo=self.DummyViewCallableA)
        self.catchall_endpoint_test(['/a', '/b'])
        self.catchall_endpoint_missing_test('/q')
    
    def test_specific_type_multiple_views(self):
        self.api_tree = {
            '/': (
                self.DummyViewCallableA(a='a'),
                self.DummyViewCallableB(b='b'),
                ),
            '/q': self.DummyViewCallableQ(),
            }
        self.prepare_catchall(target_classinfo=self.DummyViewCallableB)
        self.catchall_endpoint_test('/')
        self.catchall_endpoint_missing_test('/q')
    
    def test_multiple_types(self):
        """ 'target_classinfo' is a tuple of classes. """
        self.api_tree = {
            '/b': self.DummyViewCallableB(),
            '/c': self.DummyViewCallableC(),
            '/q': self.DummyViewCallableQ(),
            }
        self.prepare_catchall(
            target_classinfo=(self.DummyViewCallableB, self.DummyViewCallableC)
            )
        self.catchall_endpoint_test(['/b', '/c'])
        self.catchall_endpoint_missing_test('/q')
    
    def test_strict(self):
        """ When 'strict' is True, subject views must be instances of exactly
            'target_classinfo'; subclass instances are ignored. """
        self.api_tree = {
            '/a': self.DummyViewCallableA(),
            '/b': self.DummyViewCallableB(),
            }
        self.prepare_catchall(
            target_classinfo=self.DummyViewCallableA,
            strict=True,
            )
        self.catchall_endpoint_test('/a')
        self.catchall_endpoint_missing_test('/b')







