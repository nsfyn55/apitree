""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

import unittest
import pytest

from pyramid_apitree import (
    simple_view,
    function_view,
    )
from pyramid_apitree.view_callable import (
    BaseViewCallable,
    SimpleViewCallable,
    FunctionViewCallable,
    )

class Error(Exception):
    """ Base class for errors. """

class WrappedCallableWasCalledError(Error):
    """ Raised to confirm that the wrapped function was actually called by a
        view callable instance.
        
        Without testing for this error, many tests could pass without the
        wrapped callable being called at all. """

class TestBaseViewCallable(unittest.TestCase):
    """ A 'BaseViewCallable' view should have a 'view_kwargs' attribute, which
        is a dictionary of any keyword arguments provided to the decorator. """
    
    def test_no_kwargs(self):
        @BaseViewCallable
        def view_callable(request):
            pass
        
        assert hasattr(view_callable, 'view_kwargs')
        assert view_callable.view_kwargs == {}
    
    def test_yes_kwargs(self):
        PREDICATE_VALUE = object()
        @BaseViewCallable(predicate=PREDICATE_VALUE)
        def view_callable(request):
            pass
        
        assert hasattr(view_callable, 'view_kwargs')
        assert view_callable.view_kwargs == {'predicate': PREDICATE_VALUE}
    
    def test_wrapped_not_callable_raises(self):
        """ If wrapped function is not callable, an error is raised. """
        not_callable = object()
        with pytest.raises(TypeError):
            BaseViewCallable(not_callable)

class BasicBehaviorTest(object):
    """ For SimpleViewCallable and FunctionViewCallable, confirm some common
        behaviors. """
    
    def test_decorator_accepts_keyword_arguments(self):
        expected_view_kwargs = {'predicate': 'xxx'}
        view_kwargs = expected_view_kwargs.copy()
        
        @self.view_decorator(predicate='xxx')
        def view_callable(**kwargs):
            pass
        
        assert view_callable.view_kwargs == expected_view_kwargs
    
    @pytest.mark.x
    def test_return_value_unchanged(self):
        """ Return value should be returned unchanged. """
        expected = object()
        @self.view_decorator
        def view_callable(*pargs, **kwargs):
            return expected
        
        result = view_callable(MockPyramidRequest())
        
        assert result is expected

class TestSimpleViewCallableBasicBehavior(
    unittest.TestCase,
    BasicBehaviorTest,
    ):
    view_decorator = simple_view

class TestSimpleViewCallable(unittest.TestCase):
    """ A 'simple_view' view callable should have a 'view_kwargs' attribute,
        which is a dictionary of any keyword arguments provided to the
        decorator. """
    REQUEST_OBJ = object()
    
    def test_subclass_of_ViewCallable(self):
        """ Confirm that 'simple_view' is a subclass of BaseViewCallable. """
        assert issubclass(simple_view, BaseViewCallable)
    
    def test_instance_of_ViewCallable(self):
        """ Confirm that 'simple_view' returns an instance of
            BaseViewCallable. """
        @simple_view
        def view_callable(request):
            pass
        
        assert isinstance(view_callable, BaseViewCallable)
    
    def test_no_kwargs_call(self):
        """ Request value passed to callable unchanged. """
        @simple_view
        def view_callable(request):
            assert request is self.REQUEST_OBJ
        
        view_callable(self.REQUEST_OBJ)
    
    def test_yes_kwargs_call(self):
        """ Request value passed to callable unchanged. """
        @simple_view(predicate=object())
        def view_callable(request):
            assert request is self.REQUEST_OBJ
        
        view_callable(self.REQUEST_OBJ)

class MockPyramidRequest(object):
    """ A mock 'pyramid.request.Request' object. """
    def __init__(
        self,
        headers={},
        GET={},
        POST={},
        matchdict={},
        json_body={}
        ):
        self.headers = headers.copy()
        self.headers.setdefault('content-type', 'xxx')
        
        self.GET = GET.copy()
        self.POST = POST.copy()
        self.matchdict = matchdict.copy()
        
        if isinstance(json_body, dict):
            self.json_body = json_body.copy()
        else:
            self.json_body = json_body

class TestFunctionViewCallableBasicBehavior(
    unittest.TestCase,
    BasicBehaviorTest,
    ):
    view_decorator = function_view

class TestFunctionViewCallable(unittest.TestCase):
    """ A 'function_view' view callable gets function keyword arguments from the
        'request' object. """
    
    def test_subclass_of_SimpleViewCallable(self):
        assert issubclass(function_view, SimpleViewCallable)
    
    def test_instance_of_SimpleViewCallable(self):
        @function_view
        def view_callable(**kwargs):
            pass
        
        assert isinstance(view_callable, SimpleViewCallable)

class TestFunctionViewCallableRequestMethods(unittest.TestCase):
    def request_method_test(
        self,
        request_method,
        expected_kwargs=None,
        **kwargs
        ):
        method_kwargs = {'a': 1}
        if expected_kwargs is None:
            expected_kwargs = method_kwargs.copy()
        
        @function_view
        def view_callable(**kwargs):
            assert kwargs == expected_kwargs
            raise WrappedCallableWasCalledError
        
        request_kwargs = kwargs
        request_kwargs.update({request_method: method_kwargs})
        
        request = MockPyramidRequest(**request_kwargs)
        
        with pytest.raises(WrappedCallableWasCalledError):
            view_callable(request)
    
    def test_URL_kwargs(self):
        """ Keyword arguments from the URL (not from the URL query string) are
            passed through the 'matchdict' attribute of the 'request' object.
            """
        self.request_method_test('matchdict')
    
    def test_GET_kwargs(self):
        self.request_method_test('GET')
    
    def test_POST_kwargs(self):
        self.request_method_test('POST')
    
    def test_json_kwargs(self):
        """ Keyword arguments from JSON are passed through the 'json_body'
            request attribute. 'content-type' MUST be 'application/json'. """
        self.request_method_test(
            'json_body',
            headers={'content-type': 'application/json'},
            )
    
    def test_json_kwargs_wrong_content_type(self):
        """ When a request is made with an incorrect content-type (not
            'application/json'), the JSON-encoded request body will be ignored.
            """
        self.request_method_test(
            'json_body',
            headers={'content-type': 'xxx'},
            expected_kwargs={}
            )

class TestFunctionViewCallableRequestMethodsPrecedence(unittest.TestCase):
    def override_test(self, *request_methods):
        request_kwargs = {
            request_methods[i]: {'a': i}
            for i in range(len(request_methods))
            }
        
        if 'json_body' in request_kwargs:
            request_kwargs['headers'] = {'content_type': 'application/json'}
        
        # First-listed request method is expected to override the others.
        expected_value = request_kwargs[request_methods[0]]['a']
        
        request = MockPyramidRequest(**request_kwargs)
        
        @function_view
        def view_callable(a):
            assert a == expected_value
            raise WrappedCallableWasCalledError
        
        with pytest.raises(WrappedCallableWasCalledError):
            view_callable(request)
    
    def test_URL_overrides_GET(self):
        self.override_test('matchdict', 'GET')
    
    def test_URL_overrides_POST(self):
        self.override_test('matchdict', 'POST')
    
    def test_URL_overrides_JSON(self):
        self.override_test('matchdict', 'json_body')
    
    def test_GET_overrides_POST(self):
        self.override_test('GET', 'POST')
    
    def test_GET_overrides_JSON(self):
        self.override_test('GET', 'json_body')
    
    def test_URL_overrides_GET_and_POST(self):
        self.override_test('matchdict', 'GET', 'POST')
    
    def test_URL_overrides_GET_and_JSON(self):
        self.override_test('matchdict', 'GET', 'json_body')

class TestFunctionViewCallableDirectCall(unittest.TestCase):
    """ FunctionViewCallable provides a '_call' method to call the wrapped
        callable directly. This is mostly used for testing. """
    
    def make_view_callable(self):
        @function_view
        def view_callable(a=1):
            raise WrappedCallableWasCalledError
        return view_callable
    
    def test_call_unknown_kwargs_raises(self):
        """ Calling a FunctionViewCallable with a keyword argument other than
            'request' fails. """
        view_callable = self.make_view_callable()
        with pytest.raises(TypeError):
            view_callable(a=1)
    
    def test_call_direct_passes(self):
        """ Calling the '_call' method with a known keyword argument passes. """
        view_callable = self.make_view_callable()
        with pytest.raises(WrappedCallableWasCalledError):
            view_callable._call(a=1)
    
    def test_call_direct_unknown_kwarg_raises(self):
        """ Calling the '_call' method with an unknown keyword argument
            fails. """
        view_callable = self.make_view_callable()
        with pytest.raises(TypeError):
            view_callable._call(b=2)
    
    def test_call_direct_positional_args_raises(self):
        """ Calling the '_call' method with positional arguments raises an
            error. """
        view_callable = self.make_view_callable()
        with pytest.raises(TypeError):
            view_callable._call(1)







