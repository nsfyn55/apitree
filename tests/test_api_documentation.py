import unittest
import pytest
from webob import Request

from pyramid_apitree import (
    APIDocumentationView,
    api_view,
    )

@pytest.mark.a
class TestAPIDocumentationView(unittest.TestCase):
    def get_request_result(self, api_tree):
        view_callable = APIDocumentationView(api_tree)
        return view_callable(Request.blank(''))
    
    def test_empty_tree(self):
        result = self.get_request_result({})
        assert result == {}
    
    def test_endpoint_no_kwargs(self):
        @api_view
        def view_callable():
            pass
        
        result = self.get_request_result(
            {'/view': view_callable}
            )
        
        assert result == {
            '/view': {
                {
                    'required': {},
                    'optional': {},
                    'unlimited': False,
                    'returns': 'None',
                    }
                }
            }
    
    def test_endpoint_yes_kwargs(self):
        @api_view(
            required={'a': object},
            optional={'b': object},
            unlimited=True,
            returns=object,
            )
        def view_callable(**kwargs):
            pass
        
        result = self.get_request_result(
            {'/view': view_callable}
            )
        
        assert result == {
            '/view': {
                'required': {'a': object.__name__},
                'optional': {'b': object.__name__},
                'unlimited': True,
                'returns': object.__name__,
                }
            }







