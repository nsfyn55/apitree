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
        
        return self.view_call(obj)
    
    def set_wrapped(self, wrapped):
        if not callable(wrapped):
            raise TypeError('Wrapped object must be callable.')
        self.wrapped = wrapped

class SimpleViewCallable(BaseViewCallable):
    def view_call(self, request):
        return self.wrapped(request)

class FunctionViewCallable(SimpleViewCallable):
    def view_call(self, request):
        self.request = request
        
        kwargs_url = dict(request.matchdict)
        kwargs_get = dict(request.GET)
        
        content_type = request.headers.get('content-type', '').lower()
        
        if content_type == 'application/json':
            kwargs_body = request.json_body
        else:
            kwargs_body = request.POST
        
        kwargs_dict = {}
        
        # Listed in reverse-precedence order (last has highest precedence).
        kwargs_sources = [kwargs_body, kwargs_get, kwargs_url]
        
        for item in kwargs_sources:
            kwargs_dict.update(item)
        
        return self._call(**kwargs_dict)
    
    def _call(self, *pargs, **kwargs):
        if pargs:
            raise TypeError(
                "When using the '_call' method, you must provide all arguments "
                "as keyword arguments."
            )
        
        return self.wrapped(**kwargs)