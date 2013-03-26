import unittest
import pytest

from pyramid_apitree import simple_view

@pytest.mark.a
class TestSimpleViewCallable(unittest.TestCase):
    """ A 'simple_view' view callable should have a 'view_kwargs' attribute,
        which is a dictionary of any keyword arguments provided to the
        decorator.
        
        The first positional argument should always be the callable
        to-be-decorated, so 'simple_view' should be callable as a function. """
    REQUEST_OBJ = object()
    
    def make_view_callable_no_kwargs(self):
        @simple_view
        def view_callable(request):
            assert request is self.REQUEST_OBJ
        
        return view_callable
    
    def test_no_kwargs_dict(self):
        """ Empty 'view_kwargs' dict. """
        view_callable = self.make_view_callable_no_kwargs()
        
        assert hasattr(view_callable, 'view_kwargs')
        assert view_callable.view_kwargs == {}
    
    def test_no_kwargs_call(self):
        """ Request value passed to callable unchanged. """
        view_callable = self.make_view_callable_no_kwargs()
        
        view_callable(self.REQUEST_OBJ)
    
    def make_view_callable_yes_kwargs(self, **kwargs):
        @simple_view(**kwargs)
        def view_callable(request):
            assert request is self.REQUEST_OBJ
        
        return view_callable
    
    def test_yes_kwargs_dict(self):
        """ Keyword arguments stored in 'view_kwargs' dict. """
        PREDICATE_VALUE = object()
        view_callable = self.make_view_callable_yes_kwargs(
            predicate=PREDICATE_VALUE
            )
        
        assert hasattr(view_callable, 'view_kwargs')
        assert view_callable.view_kwargs == {'predicate': PREDICATE_VALUE}
    
    def test_yes_kwargs_call(self):
        """ Request value passed to callable unchanged. """
        view_callable = self.make_view_callable_yes_kwargs(a=1)
        
        view_callable(self.REQUEST_OBJ)







