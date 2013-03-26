""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

import unittest
import pytest

from pyramid_apitree import (
    simple_view,
    function_view,
    )
from pyramid_apitree.view_callable import BaseViewCallable

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

@pytest.mark.a
class TestSimpleViewCallable(unittest.TestCase):
    """ A 'simple_view' view callable should have a 'view_kwargs' attribute,
        which is a dictionary of any keyword arguments provided to the
        decorator.
        
        The first positional argument should always be the callable
        to-be-decorated, so 'simple_view' should be callable as a function. """
    REQUEST_OBJ = object()
    
    def test_subclass_of_ViewCallable(self):
        """ Confirm that 'simple_view' is a subclass of ViewCallable.
            
            This is necessary to confirm that the logic of the base ViewCallable
            class is being tested. """
        assert issubclass(simple_view, BaseViewCallable)
    
    def test_instance_of_ViewCallable(self):
        """ Confirm that 'simple_view' returns instances of ViewCallable. """
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
    
    
    







