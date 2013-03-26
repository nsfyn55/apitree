""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

class BaseViewCallable(object):
    def __init__(self, *pargs, **kwargs):
        if pargs:
            self.set_wrapped(pargs[0])
        
        self.view_kwargs = kwargs
    
    def __call__(self, obj):
        if not hasattr(self, 'wrapped'):
            self.set_wrapped(obj)
            return self
        
        self.view_call(obj)
    
    def set_wrapped(self, wrapped):
        if not callable(wrapped):
            raise TypeError('Wrapped object must be callable.')
        self.wrapped = wrapped

class SimpleViewCallable(BaseViewCallable):
    def view_call(self, request):
        return self.wrapped(request)

class FunctionViewCallable(SimpleViewCallable):
    pass