import json
import unittest
import pytest
from webob import Request

from iomanager import ListOf
from pyramid_apitree import api_view
from pyramid_apitree.api_documentation import (
    APIDocumentationView,
    PreparationFailureError,
    )

pytestmark = pytest.mark.a

def prep_json(s, n=0, **kwargs):
    kwargs.setdefault('indent', 4)
    json_s = json.dumps(s, **kwargs).replace("'", '').replace('"', '')
    return '\n'.join("    " * n + line for line in  json_s.splitlines())

class TestPrepareItem(unittest.TestCase):
    """ Test the function which prepares the API documentation result by
        converting class objects to name-strings. """
    def setUp(self):
        self.apidoc_view = APIDocumentationView()
    
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
        
        class CustomAPIDocumentationView(APIDocumentationView):
            transformations = {
                CustomType: transformation_obj,
                }
        
        api_doc_view = CustomAPIDocumentationView()
        
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
    
    @pytest.mark.b
    def test_default_transform(self):
        """ Default 'transform' method should call 'iospec' method of item being
            prepared. """
        string_result = self.STRING_RESULT
        class CustomType(object):
            @classmethod
            def iospec(cls):
                return string_result
        
        api_doc_view = APIDocumentationView()
        
        assert api_doc_view.prepare(CustomType) == string_result
    
    def test_custom_transform(self):
        string_result = self.STRING_RESULT
        class CustomAPIDocumentationView(APIDocumentationView):
            def transform(self, value):
                return string_result
        
        api_doc_view = CustomAPIDocumentationView()
        
        assert api_doc_view.prepare(object) == string_result
    
    @pytest.mark.c
    def test_transform_container_result(self):
        """ When a transformation function or 'transform' method returns a
            container, that container should also be passed to 'prepare'. """
        container_result = {'a': object}
        
        class CustomType(object):
            pass
        
        def transform_function(value):
            return container_result.copy()
        
        class CustomAPIDocumentationView(APIDocumentationView):
            transformations = {
                CustomType: transform_function
                }
        
        api_doc_view = CustomAPIDocumentationView()
        
        result = api_doc_view.prepare(CustomType)
        expected = api_doc_view.prepare(container_result.copy())
        
        assert result == expected







