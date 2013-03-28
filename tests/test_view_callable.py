""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

import unittest
import pytest
import ioprocess

from pyramid_apitree import (
    simple_view,
    function_view,
    api_view,
    )
from pyramid_apitree.view_callable import (
    BaseViewCallable,
    SimpleViewCallable,
    FunctionViewCallable,
    APIViewCallable,
    )

class Error(Exception):
    """ Base class for errors. """

class WrappedCallableSuccessError(Error):
    """ Raised to confirm that the wrapped function was actually called by a
        view callable instance.
        
        Without testing for this error, many tests could pass without the
        wrapped callable being called at all. """

class TestBaseViewCallable(unittest.TestCase):
    """ A 'BaseViewCallable' view should have a 'view_kwargs' attribute, which
        is a dictionary of any keyword arguments provided to the decorator. """
    
    def view_kwargs_test(self, view_callable, expected_view_kwargs):
        assert hasattr(view_callable, 'view_kwargs')
        assert view_callable.view_kwargs == expected_view_kwargs
    
    def test_no_kwargs(self):
        @BaseViewCallable
        def view_callable(request):
            pass
        
        self.view_kwargs_test(view_callable, {})
        #assert hasattr(view_callable, 'view_kwargs')
        #assert view_callable.view_kwargs == {}
    
    def test_empty_kwargs(self):
        @BaseViewCallable()
        def view_callable(request):
            pass
        
        self.view_kwargs_test(view_callable, {})
        #assert hasattr(view_callable, 'view_kwargs')
        #assert view_callable.view_kwargs == {}
    
    def test_yes_kwargs(self):
        PREDICATE_VALUE = object()
        @BaseViewCallable(predicate=PREDICATE_VALUE)
        def view_callable(request):
            pass
        
        self.view_kwargs_test(view_callable, {'predicate': PREDICATE_VALUE})
        #assert hasattr(view_callable, 'view_kwargs')
        #assert view_callable.view_kwargs == {'predicate': PREDICATE_VALUE}
    
    def test_wrapped_not_callable_raises(self):
        """ If wrapped function is not callable, an error is raised. """
        not_callable = object()
        with pytest.raises(TypeError):
            BaseViewCallable(not_callable)

class BasicBehaviorTest(object):
    """ For all view callable classes, confirm some common behaviors. """
    
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
    
    def test_subclass_of_BaseViewCallable(self):
        """ Confirm that 'simple_view' is a subclass of BaseViewCallable. """
        assert issubclass(simple_view, BaseViewCallable)
    
    def test_instance_of_BaseViewCallable(self):
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
    
    def test_subclass_of_BaseViewCallable(self):
        assert issubclass(function_view, BaseViewCallable)
    
    def test_instance_of_BaseViewCallable(self):
        @function_view
        def view_callable(**kwargs):
            pass
        
        assert isinstance(view_callable, BaseViewCallable)

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
            raise WrappedCallableSuccessError
        
        request_kwargs = kwargs
        request_kwargs.update({request_method: method_kwargs})
        
        request = MockPyramidRequest(**request_kwargs)
        
        with pytest.raises(WrappedCallableSuccessError):
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
            raise WrappedCallableSuccessError
        
        with pytest.raises(WrappedCallableSuccessError):
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
            raise WrappedCallableSuccessError
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
        with pytest.raises(WrappedCallableSuccessError):
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

class TestAPIViewCallableBasicBehavior(
    unittest.TestCase,
    BasicBehaviorTest,
    ):
    view_decorator = api_view
    
    def test_ioprocess_kwargs_collected(self):
        """ Confirm that the special keyword arguments input/output processing
            are not included in the 'view_kwargs' dictionary. """
        ioprocess_kwargs = dict(
            required=object(),
            optional=object(),
            unlimited=object(),
            returns=object(),
            )
        view_kwargs = dict(
            predicate=object()
            )
        decorator_kwargs = ioprocess_kwargs.copy()
        decorator_kwargs.update(view_kwargs)
        
        @api_view(**decorator_kwargs)
        def view_callable():
            pass
        
        assert view_callable.view_kwargs == view_kwargs

@pytest.mark.c
class TestAPIViewCallableIOProcessInput(unittest.TestCase):
    """ Confirm that 'IOProcessor.process' is being called to process input
        values.
        
        Confirm that keyword arguments for 'IOProcessor.process' can be passed
        through the decorator.
        
        Confirm that parameters specifed in the wrapped callable definition and
        parameters specified in the decorator interact with each other in the
        correct way.
        
        Confirm that the 'unlimited' decorator argument behaves in the expected
        way. """
    
    def call_passes_test(self, view_callable, **kwargs):
        with pytest.raises(WrappedCallableSuccessError):
            view_callable._call(**kwargs)
    
    def call_raises_test(self, view_callable, **kwargs):
        with pytest.raises(ioprocess.IOProcessFailureError):
            view_callable._call(**kwargs)
    
    def test_no_kwargs_passes(self):
        @api_view
        def view_callable():
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable)
    
    def test_unknown_kwarg_raises(self):
        @api_view
        def view_callable():
            pass
        
        self.call_raises_test(view_callable, a=None)
    
    def test_definition_required_present_passes(self):
        @api_view
        def view_callable(a):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=None)
    
    def test_definition_required_missing_raises(self):
        @api_view
        def view_callable(a):
            pass
        
        self.call_raises_test(view_callable)
    
    def test_definition_optional_present_passes(self):
        @api_view
        def view_callable(a=None):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=None)
    
    def test_definition_optional_missing_passes(self):
        @api_view
        def view_callable(a=None):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable)
    
    def test_decorator_required_present_passes(self):
        @api_view(required={'a': object})
        def view_callable(**kwargs):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=None)
    
    def test_decorator_required_missing_raises(self):
        @api_view(required={'a': object})
        def view_callable(**kwargs):
            pass
        
        self.call_raises_test(view_callable)
    
    def test_decorator_optional_present_passes(self):
        @api_view(optional={'a': object})
        def view_callable(**kwargs):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=None)
    
    def test_decorator_optional_missing_passes(self):
        @api_view(optional={'a': object})
        def view_callable(**kwargs):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable)
    
    def test_decorator_optional_not_in_definition_raises(self):
        @api_view(optional={'a': object})
        def view_callable():
            pass
        
        self.call_raises_test(view_callable, a=None)
    
    def test_decorator_required_not_in_definition_raises(self):
        @api_view(required={'a': object})
        def view_callable():
            pass
        
        self.call_raises_test(view_callable, a=None)
    
    def test_decorator_required_overrides_definition_optional(self):
        @api_view(required={'a': object})
        def view_callable(a=None):
            pass
        
        self.call_raises_test(view_callable)
    
    def test_decorator_optional_overrides_definition_required(self):
        @api_view(optional={'a': object})
        def view_callable(a):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable)
    
    def test_decorator_required_compliments_definition_required(self):
        @api_view(required={'b': object})
        def view_callable(a, **kwargs):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=None, b=None)
    
    def test_decorator_optional_compliments_definition_optional(self):
        @api_view(optional={'b': object})
        def view_callable(a=None, **kwargs):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=None, b=None)
    
    def test_definition_kwargs_not_unlimited(self):
        """ When the view callable definition specifies a '**kwargs' parameter
            and the 'unlimited' directive is not used, unknown keyword arguments
            fail. """
        @api_view
        def view_callable(**kwargs):
            pass
        
        self.call_raises_test(view_callable, a=None)
    
    def test_decorator_unlimited_passes_with_definition_kwargs(self):
        """ When 'unlimited=True' AND the view callable definition specifies a
            '**kwargs' parameter, unknown keyword arguments pass. """
        @api_view(unlimited=True)
        def view_callable(**kwargs):
            raise WrappedCallableSuccessError
        
        self.call_passes_test(view_callable, a=None)
    
    def test_decorator_unlimited_raises_without_definition_kwargs(self):
        """ When 'unlimited=True' but the view callable definition does not
            specify a '**kwargs' parameter, unknown keyword argumets fail. """
        @api_view(unlimited=True)
        def view_callable():
            pass
        
        self.call_raises_test(view_callable, a=None)

@pytest.mark.b
class TestAPIViewCallableIOProcessOutput(unittest.TestCase):
    """ Confirm that 'IOProcessor.process' is being called for view callable
        output.
        
        All 'output' values are considered to be 'required': output checking is
        strict. """
    
    def test_item_present_passes(self):
        @api_view(returns={'a': object})
        def view_callable():
            return {'a': None}
        
        result = view_callable._call

class CustomInputType(object):
    """ A custom type for testing coercion. """

class CustomCoercedType(object):
    """ A custom type for testingcoercion. """

class CustomOutputType(object):
    """ A custom type for testing output coercion. """

@pytest.mark.a
class TestAPIViewCallableCoercion(unittest.TestCase):
    class CustomAPIViewCallable(APIViewCallable):
        """ A view callable that coerces input and output value types. """
        @property
        def input_coercion_functions(self):
            def coerce_custom_input(value):
                if isinstance(value, CustomInputType):
                    return CustomCoercedType()
                raise ioprocess.CoercionFailureError
            return {CustomCoercedType: coerce_custom_input}
        
        @property
        def output_coercion_functions(self):
            def coerce_custom_output(value):
                if isinstance(value, CustomCoercedType):
                    return CustomOutputType()
                raise ioprocess.CoercionFailureError
            return {CustomCoercedType: coerce_custom_output}
    
    def test_input_coercion(self):
        """ 'wrapped_call' coerces input. """
        @self.CustomAPIViewCallable(
            required={'a': CustomCoercedType}
            )
        def view_callable(a):
            assert isinstance(a, CustomCoercedType)
            raise WrappedCallableSuccessError
        
        with pytest.raises(WrappedCallableSuccessError):
            view_callable.wrapped_call(a=CustomInputType())
    
    def test_output_coercion(self):
        """ 'wrapped_call' coerces output. """
        @self.CustomAPIViewCallable(
            returns=CustomCoercedType
            )
        def view_callable():
            return CustomCoercedType()
        
        result = view_callable.wrapped_call()
        assert isinstance(result, CustomOutputType)
    
    def test_input_coercion_only_for_special_call(self):
        """ '_call' coerces input, but not output. """
        @self.CustomAPIViewCallable(
            required={'a': CustomCoercedType},
            returns=CustomCoercedType,
            )
        def view_callable(a):
            assert isinstance(a, CustomCoercedType)
            return a
        
        result = view_callable._call(a=CustomInputType())
        assert isinstance(result, CustomCoercedType)







