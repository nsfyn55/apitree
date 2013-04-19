import json
import unittest
import pytest
from webob import Request

from iomanager import ListOf
from pyramid_apitree import (
    APIViewCallable,
    SimpleViewCallable,
    simple_view,
    function_view,
    api_view,
    )
from pyramid_apitree.api_documentation import (
    APIDocumentationMaker,
    PreparationFailureError,
    )

def prep_json(s, n=0, **kwargs):
    kwargs.setdefault('indent', 4)
    json_s = json.dumps(s, **kwargs).replace("'", '').replace('"', '')
    return '\n'.join("    " * n + line for line in  json_s.splitlines())

class TestPrepareItem(unittest.TestCase):
    """ Test the function which prepares the API documentation result by
        converting class objects to name-strings. """
    def setUp(self):
        self.apidoc_view = APIDocumentationMaker()
    
    def test_custom_class(self):
        class CustomClass(object):
            pass
        
        assert self.apidoc_view.prepare(CustomClass) == 'CustomClass'
    
    def test_dict_obj(self):
        expected = prep_json({'a': 'object'})
        result = self.apidoc_view.prepare({'a': object})
        assert result == expected
    
    def test_list_obj(self):
        expected = prep_json(['object'])
        result = self.apidoc_view.prepare([object])
        assert result == expected
    
    def test_dict_list(self):
        expected = prep_json({'a': ['object']})
        result = self.apidoc_view.prepare({'a': [object]})
        assert result == expected
    
    def test_list_dict(self):
        expected = prep_json([{'a': 'object'}])
        result = self.apidoc_view.prepare([{'a': object}])
        assert result == expected
    
    def test_listof_object(self):
        assert self.apidoc_view.prepare(ListOf(object)) == 'ListOf(object)'
    
    def test_listof_list(self):
        expected = (
            'ListOf(\n' +
            prep_json(['object'], 1) + '\n'
            +')'
            )
        result = self.apidoc_view.prepare(ListOf([object]))
        assert result == expected
    
    def test_listof_dict(self):
        expected = (
            "ListOf(\n"
            + prep_json({'a': 'object'}, 1) + '\n'
            + ')'
            )
        result = self.apidoc_view.prepare(ListOf({'a': object}))
        assert result == expected

class TestPrepareItemCustomClassName(unittest.TestCase):
    def test_display_name(self):
        expected = u'abcxyz'
        class CustomType(object):
            pass
        
        class CustomAPIDocumentationMaker(APIDocumentationMaker):
            display_names = {
                CustomType: expected
                }
        
        api_doc_view = CustomAPIDocumentationMaker()
        
        assert api_doc_view.prepare(CustomType) == expected

class TestCreateDocumentationViewAttributes(unittest.TestCase):
    """ When 'APIDocumentationMaker' processes an 'api_tree' dictionary, confirm
        that each view callable's attributes are correctly included. """
    
    def view_test(self, *keys):
        decorator_values = {
            'required': {'x': object},
            'optional': {'y': object},
            'unlimited': True,
            'returns': object,
            }
        decorator_kwargs = {ikey: decorator_values[ikey] for ikey in keys}
        
        @api_view(**decorator_kwargs)
        def view_callable(**kwargs):
            pass
        
        api_tree = {'/': {'GET': view_callable}}
        
        documentation = APIDocumentationMaker().create_documentation(api_tree)
        
        view_dict = documentation['/']['GET']
        
        view_dict.pop('description', None)
        
        assert set(keys) == set(view_dict.keys())
    
    def test_required(self):
        self.view_test('required')
    
    def test_optional(self):
        self.view_test('optional')
    
    def test_unlimited(self):
        self.view_test('unlimited')
    
    def test_returns(self):
        self.view_test('returns')
    
    def test_all(self):
        self.view_test('required', 'optional', 'unlimited', 'returns')

class TestCreateDocumentationSkipSpecialKeys(unittest.TestCase):
    """ 'create_documentation' filters out 'special_kwargs' keys from 'required'
        and 'optional'.
        
        Keyword arguments provided by 'special_kwargs' are usually provided
        programatically, so they should not be exposed in the API
        documentation. """
    
    def make_api_tree(self, parameter_kind):
        class CustomViewCallable(APIViewCallable):
            def special_kwargs(self):
                return {'x': object()}
        
        @CustomViewCallable(**{parameter_kind: {'x': object}})
        def view_callable(**kwargs):
            pass
        
        api_tree = {'/': {'GET': view_callable}}
        
        return api_tree
    
    def skip_keys_test(self, parameter_kind):
        api_tree = self.make_api_tree(parameter_kind)
        
        documentation = APIDocumentationMaker().create_documentation(api_tree)
        
        view_dict = documentation['/']['GET'].copy()
        del view_dict['description']
        
        assert view_dict == {}
    
    def test_skip_keys_required(self):
        self.skip_keys_test('required')
    
    def test_skip_keys_optional(self):
        self.skip_keys_test('optional')
    
    def no_mutation_test(self, parameter_kind):
        """ Confirm that this behavior does not mutate the iospec dictionaries
            of the view-callable's IOManager in-place. """
        api_tree = self.make_api_tree(parameter_kind)
        
        view_callable = api_tree['/']['GET']
        
        # Confirm that '_call' works before 'create_documentation'.
        view_callable._call(x=object())
        
        APIDocumentationMaker().create_documentation(api_tree)
        
        # Confirm that '_call' works after 'create_documentation'.
        view_callable._call(x=object())
    
    def test_no_mutation_required(self):
        self.no_mutation_test('required')
    
    def test_no_mutation_optional(self):
        self.no_mutation_test('optional')

class TestCreateDocumentationViewCallables(unittest.TestCase):
    """ Confirm that 'create_documentation' is able to handle view callables of
        every type included in 'pyramid_apitree', without raising any
        errors. """
    
    def view_callable_test(self, view_callable_class):
        @view_callable_class
        def view_callable():
            pass
        
        api_tree = {'/': view_callable}
        
        APIDocumentationMaker().create_documentation(api_tree)
    
    def test_simple_view(self):
        self.view_callable_test(simple_view)
    
    def test_function_view(self):
        self.view_callable_test(function_view)
    
    def test_api_view(self):
        self.view_callable_test(api_view)

class TestAPIDocumentationMaker(unittest.TestCase):
    """ Confirm that when APIDocumentationMaker initializes, views are correctly
        discovered. """
    def make_view_callable(self):
        @api_view
        def view_callable(**kwargs):
            pass
        
        return view_callable
    
    def get_documentation_dict_result(
        self,
        api_tree,
        api_doc_view_class=APIDocumentationMaker
        ):
        api_doc_view = api_doc_view_class(api_tree)
        
        return api_doc_view.documentation_dict
    
    def location_found_test(self, api_tree, location):
        result = self.get_documentation_dict_result(api_tree)
        for ikey in location:
            # Confirm that the expected location is included in the result.
            assert ikey in result
            result = result[ikey]
        # End of test.
    
    def location_missing_test(self, api_tree, location):
        missing_location = location.pop(-1)
        result = self.get_documentation_dict_result(api_tree)
        for ikey in location:
            result = result[ikey]
        
        assert missing_location not in result
    
    def test_empty(self):
        self.location_found_test({}, [])
    
    def request_method_test(self, request_methods):
        api_tree = {
            '/': {request_methods: self.make_view_callable()}
            }
        request_methods_string = ', '.join(request_methods)
        
        self.location_found_test(api_tree, ['/', request_methods_string])
    
    def test_single_request_method(self):
        self.request_method_test(('GET',))
    
    def test_multiple_request_methods(self):
        self.request_method_test(('GET', 'POST'))
    
    def test_types_to_skip(self):
        class CustomViewCallable(APIViewCallable):
            pass
        
        class CustomAPIDocumentationMaker(APIDocumentationMaker):
            types_to_skip = [CustomViewCallable]
        
        @CustomViewCallable
        def trial_view():
            pass
        
        api_tree = {
            '/': trial_view
            }
        
        result = self.get_documentation_dict_result(
            api_tree,
            api_doc_view_class=CustomAPIDocumentationMaker,
            )
        
        assert result == {}

class MockConfigurator(object):
    """ A mocked Pyramid configurator. """
    def __init__(self):
        self.views = {}
        self.routes = set()
    
    def add_view(
        self,
        view,
        route_name,
        request_method,
        accept=None,
        **kwargs
        ):
        view_dict = kwargs
        view_dict['view_callable'] = view
        
        route_dict = self.views.setdefault(route_name, dict())
        
        method_dict = route_dict.setdefault(request_method, dict())
        
        method_dict[accept] = view_dict
    
    def add_route(self, name, pattern):
        assert name == pattern
        self.routes.add(pattern)

class TestAPIDocumentationMakerAddDocumentation(unittest.TestCase):
    PATH = '/api_docs'
    
    def add_documentation_test(
        self,
        api_doc_maker_class,
        api_doc_view_class
        ):
        """ Test the 'instert_documentation' classmethod of
            'APIDocumentationmaker'. """
        api_tree = {}
        config = MockConfigurator()
        
        api_doc_maker_class.add_documentation_views(
            config,
            api_tree,
            self.PATH,
            )
        
        views = config.views[self.PATH]['GET']
        
        for iaccept in [None, 'application/json']:
            assert isinstance(
                views[iaccept]['view_callable'],
                api_doc_view_class
                )
        
        assert views['application/json']['renderer'] == 'json'
    
    def test_add_documentation(self):
        self.add_documentation_test(
            APIDocumentationMaker,
            SimpleViewCallable,
            )
    
    def test_custom_view_callable_class(self):
        class CustomViewCallable(SimpleViewCallable):
            pass
        
        class CustomAPIDocumentationMaker(APIDocumentationMaker):
            documentation_view_class = CustomViewCallable
        
        self.add_documentation_test(
            CustomAPIDocumentationMaker,
            CustomViewCallable,
            )







