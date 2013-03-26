def simple_view(*pargs, **kwargs):
    if pargs:
        wrapped = pargs[0]
        wrapped.view_kwargs = {}
        return wrapped
    
    def inner_decorator(wrapped):
        wrapped.view_kwargs = kwargs
        return wrapped
    
    return inner_decorator