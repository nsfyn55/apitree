""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

class BaseViewCallable(object):
    def __init__(self, *pargs, **kwargs):
        if pargs:
            self.set_wrapped(pargs[0])
        
        self.stash_kwargs(kwargs)
    
    def __call__(self, obj):
        if not hasattr(self, 'wrapped'):
            self.set_wrapped(obj)
            return self
        
        return self.view_call(obj)
    
    def stash_kwargs(self, kwargs_dict):
        self.view_kwargs = kwargs_dict
    
    def set_wrapped(self, wrapped):
        if not callable(wrapped):
            raise TypeError('Wrapped object must be callable.')
        self.wrapped = wrapped

class SimpleViewCallable(BaseViewCallable):
    def view_call(self, request):
        return self.wrapped(request)

class FunctionViewCallable(BaseViewCallable):
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
        special_kwargs = self.special_kwargs(request)
        
        # Listed in reverse-precedence order (last has highest precedence).
        kwargs_sources = [kwargs_body, kwargs_get, kwargs_url, special_kwargs]
        
        for item in kwargs_sources:
            kwargs_dict.update(item)
        
        #return self._call(**kwargs_dict)
        return self.wrapped_call(**kwargs_dict)
    
    def special_kwargs(self, request):
        return {}
    
    def wrapped_call(self, **kwargs):
        return self._call(**kwargs)
    
    def _call(self, *pargs, **kwargs):
        if pargs:
            raise TypeError(
                "When using the '_call' method, you must provide all arguments "
                "as keyword arguments."
            )
        
        return self.wrapped(**kwargs)

class APIViewCallable(FunctionViewCallable):
    def get_items_from_dict(self, dict_obj, keys, result_keys=None):
        if result_keys is None:
            result_keys = list(keys)
        result = {}
        for ikey, result_key in zip(keys, result_keys):
            try:
                result[result_key] = dict_obj[ikey]
            except KeyError:
                continue
        return result
    
    def stash_kwargs(self, kwargs_dict):
        """ Stash kwargs dicts for input/output processing. """
        self.verify_input_kwargs = self.get_items_from_dict(
            kwargs_dict,
            ['required', 'optional', 'unlimited'],
            )
        
        self.coerce_input_kwargs = self.get_items_from_dict(
            kwargs_dict,
            ['required', 'optional'],
            )
        
        self.process_output_kwargs = self.get_items_from_dict(
            kwargs_dict,
            ['returns'],
            ['required']
            )
        
        remaining_kwargs = {
            ikey: ivalue for ikey, ivalue in kwargs_dict.iteritems()
            if ikey not in ['required', 'optional', 'unlimited', 'returns']
            }
        
        super(APIViewCallable, self).stash_kwargs(remaining_kwargs)







