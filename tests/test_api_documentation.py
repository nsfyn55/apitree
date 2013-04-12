import json
import unittest
import pytest
from webob import Request

from iomanager import ListOf
from pyramid_apitree import (
    APIViewCallable,
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
    STRING_RESULT = u'abcxyz'
    
    def transformation_test(self, transformation_obj, expected=None):
        class CustomType(object):
            pass
        
        class CustomAPIDocumentationMaker(APIDocumentationMaker):
            transformations = {
                CustomType: transformation_obj,
                }
        
        api_doc_view = CustomAPIDocumentationMaker()
        
        assert api_doc_view.prepare(CustomType) == expected
    
    def test_custom_class_name(self):
        self.transformation_test(self.STRING_RESULT, self.STRING_RESULT)
    
    def test_custom_function(self):
        def transform_custom(value):
            return self.STRING_RESULT
        
        self.transformation_test(transform_custom, self.STRING_RESULT)
    
    def test_custom_function_failure(self):
        """ Custom transformation function fails to produce a string result. """
        def transform_custom(value):
            return object()
        
        with pytest.raises(PreparationFailureError):
            self.transformation_test(transform_custom)
    
    def test_default_transform(self):
        """ Default 'transform' method should call 'iospec' method of item being
            prepared. """
        string_result = self.STRING_RESULT
        class CustomType(object):
            @classmethod
            def iospec(cls):
                return string_result
        
        api_doc_view = APIDocumentationMaker()
        
        assert api_doc_view.prepare(CustomType) == string_result
    
    def test_custom_transform(self):
        string_result = self.STRING_RESULT
        class CustomAPIDocumentationMaker(APIDocumentationMaker):
            def transform(self, value):
                return string_result
        
        api_doc_view = CustomAPIDocumentationMaker()
        
        assert api_doc_view.prepare(object) == string_result
    
    def test_transform_container_result(self):
        """ When a transformation function or 'transform' method returns a
            container, that container should also be passed to 'prepare'. """
        container_result = {'a': object}
        
        class CustomType(object):
            pass
        
        def transform_function(value):
            return container_result.copy()
        
        class CustomAPIDocumentationMaker(APIDocumentationMaker):
            transformations = {
                CustomType: transform_function
                }
        
        api_doc_view = CustomAPIDocumentationMaker()
        
        result = api_doc_view.prepare(CustomType)
        expected = api_doc_view.prepare(container_result.copy())
        
        assert result == expected

class TestCreateDocumentation(unittest.TestCase):
    """ When 'APIDocumentationMaker' processes an 'api_tree' dictionary, confirm
        that each view callable's attributes are correctly included. """
    
    def view_test(self, *keys):
        decorator_values = {
            'required': object,
            'optional': object,
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

class TestAPIDocumentationMaker(unittest.TestCase):
    """ Confirm that when APIDocumentationMaker initializes, views are correctly
        discovered. """
    def make_view_callable(self):
        @api_view
        def view_callable(**kwargs):
            pass
        
        return view_callable
    
    def get_documentation_tree_result(
        self,
        api_tree,
        api_doc_view_class=APIDocumentationMaker
        ):
        api_doc_view = api_doc_view_class(api_tree)
        
        return api_doc_view.documentation_tree
    
    def location_found_test(self, api_tree, location):
        result = self.get_documentation_tree_result(api_tree)
        for ikey in location:
            # Confirm that the expected location is included in the result.
            assert ikey in result
            result = result[ikey]
        # End of test.
    
    def location_missing_test(self, api_tree, location):
        missing_location = location.pop(-1)
        result = self.get_documentation_tree_result(api_tree)
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
        
        result = self.get_documentation_tree_result(
            api_tree,
            api_doc_view_class=CustomAPIDocumentationMaker,
            )
        
        assert result == {}
    
    @pytest.mark.a
    def test_scan_and_insert(self):
        """ Test the 'scan_and_insert' classmethod of
            'APIDocumentationMaker'. """
        class CustomAPIViewCallable(APIViewCallable):
            pass
        
        api_tree = {'/view': self.make_view_callable()}
        
        APIDocumentationMaker.scan_and_insert(
            api_tree,
            '/apidoc',
            CustomAPIViewCallable,
            )
        
        result = api_tree['/apidoc'][0]
        assert isinstance(result, CustomAPIViewCallable)







