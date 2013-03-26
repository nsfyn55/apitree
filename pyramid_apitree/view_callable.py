""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

class BaseViewCallable(object):
    pass

class SimpleViewCallable(BaseViewCallable):
    pass

def simple_view(*pargs, **kwargs):
    if pargs:
        wrapped = pargs[0]
        wrapped.view_kwargs = {}
        return wrapped
    
    def inner_decorator(wrapped):
        wrapped.view_kwargs = kwargs
        return wrapped
    
    return inner_decorator

class FunctionViewCallable(BaseViewCallable):
    pass