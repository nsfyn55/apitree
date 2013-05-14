""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

from collections.abc import (
    Sequence,
    Mapping,
    )
from .exc import (
    APITreeError,
    APITreeStructureError,
    )
from .util import is_container

class RequestMethod(object):
    """ Represents a request method predicate in an API tree. """
    def __init__(self, *request_method):
        """ 'request_method' is always a tuple. This behavior is consistent
            with how the 'request_method' predicate is handled within
            Pyramid. """
        self.request_method = request_method
    
    def __add__(self, other):
        combined = self.request_method + other.request_method
        return RequestMethod(*combined)

ALL_REQUEST_METHOD_STRINGS = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']

GET, POST, PUT, DELETE, HEAD = tuple(
    map(RequestMethod, ALL_REQUEST_METHOD_STRINGS)
    )

def conglomerate_endpoints(endpoints_dicts_list):
    result = {}
    for endpoints_dict in endpoints_dicts_list:
        for ikey, ivalue in endpoints_dict.items():
            views_list = result.setdefault(ikey, list())
            views_list.extend(ivalue)
    return result

def parse_branch(branch_location, branch_obj, root_path):
    """ Return value has the same format as 'get_endpoints'. """
    
    # ---------------------- Parse 'branch_location'. ----------------------
    
    if is_container(branch_location, Sequence):
        if all(
            [isinstance(item, RequestMethod) for item in branch_location]
            ):
            # 'branch_location' is a tuple of request methods. Sum to a single
            # request method.
            branch_location = sum(branch_location, RequestMethod())
            
        else:
            result_list = [
                parse_branch(item, branch_obj, root_path)
                for item in branch_location
                ]
            return conglomerate_endpoints(result_list)
    
    if isinstance(branch_location, RequestMethod):
        request_method = branch_location.request_method
        branch_path = ''
    else:
        request_method = None
        branch_path = branch_location
    
    try:
        complete_route = root_path + branch_path
    except TypeError:
        raise APITreeError(
            "Invalid branch route object. Must be one of: a string path "
            "component ('/something'); a RequestMethod instance; or a "
            "tuple of those. Got: {}"
            .format(type(branch_path).__name__)
            )
    
    # ----------------------- Parse 'branch_object'. -----------------------
    
    if is_container(branch_obj, Sequence):
        try:
            return get_endpoints(branch_obj, complete_route)
        except APITreeStructureError:
            pass
        
        result_list = [
            parse_branch(branch_location, item, root_path)
            for item in branch_obj
            ]
        return conglomerate_endpoints(result_list)
    
    if isinstance(branch_obj, Mapping):
        if request_method is not None:
            invalid_path = complete_route + '/' + str(request_method)
            raise APITreeError(
                "RequestMethod-instance branch routes (GET, POST, etc.) "
                "cannot have a dictionary of sub-routes. Invalid path: {}"
                .format(invalid_path)
                )
        
        return get_endpoints(branch_obj, complete_route)
    
    # ------------- 'branch_object' is a single view callable. -------------
    
    view_dict = {}
    
    view_callable = branch_obj
    
    view_kwargs = getattr(view_callable, 'view_kwargs', dict())
    view_dict.update(view_kwargs)
    view_dict['view'] = view_callable
    
    # Request method from API tree overrides request method provided by
    # view callable 'view_kwargs'.
    if request_method is not None:
        view_dict['request_method'] = request_method
    
    return {complete_route: [view_dict]}

def get_pairs(api_tree):
    """ 'api_tree' must be either a dictionary or a list of 2-length tuples. """
    try:
        return api_tree.items()
    except AttributeError:
        pass
    
    try:
        return [(a, b) for a, b in api_tree]
    except (TypeError, ValueError):
        raise APITreeStructureError(
            "'api_tree' value was not traversable. 'api_tree' must be either a "
            "dictionary or a sequence of 2-length tuples. Got: {}"
            .format(api_tree)
            )
    
def get_endpoints(api_tree, root_path=''):
    """ Returns a dictionary, like this:
        {
            'complete/route': [
                {
                    'view': view_callable,
                    'predicate': predicate_value,
                    ...
                    },
                <One 'view callable' dictionary for each request method.> ...
                ]
            }
        
        """
    pairs = get_pairs(api_tree)
    
    result_list = [
        parse_branch(branch_location, branch_object, root_path)
        for branch_location, branch_object in pairs
        ]
    return conglomerate_endpoints(result_list)

def scan_api_tree(configurator, api_tree, root_path=''):
    endpoints = get_endpoints(api_tree, root_path=root_path)
    
    for complete_route, view_dicts_list in endpoints.items():
        configurator.add_route(name=complete_route, pattern=complete_route)
        
        for view_dict in view_dicts_list:
            configurator.add_view(
                route_name=complete_route,
                **view_dict
                )

def add_catchall(
    configurator,
    api_tree,
    catchall,
    view_kwargs=None,
    additional_view_kwargs={},
    target_classinfo=None,
    strict=False,
    ):
    """ Add a 'catchall' view callable to an API tree.
        
        By default, the catchall is added to every route in the API tree.
        
        If 'target_class' is specified, the catchall will only be added to
        routes where a view callable of 'target_class' has been registered.
        
        'catchall' MUST have distinct predicates for EVERY route where it will
        be registered; otherwise a pyramid.exceptions.ConfigurationError will
        be raised. """
    
    def get_catchall_kwargs(
        catchall, view_dicts_list, view_kwargs, additional_view_kwargs
        ):
        request_method_list = []
        for imethod in [
            item.get('request_method', tuple()) for item in view_dicts_list
            ]:
            if not is_container(imethod, Sequence):
                imethod = (imethod, )
            request_method_list.extend(imethod)
        request_method = tuple(set(request_method_list))
        
        result = {'custom_predicates': (catchall.catchall_custom_predicate, )}
        
        if request_method:
            result.update({'request_method': request_method})
        
        if view_kwargs:
            result.update(view_kwargs)
        else:
            result.update(getattr(catchall, 'view_kwargs', {}))
        
        result.update(additional_view_kwargs)
        
        return result
    
    def strict_test(view_dict):
        subject_type = type(view_dict['view'])
        for iclass in target_classinfo:
            if subject_type is iclass:
                return True
        return False
    
    def nonstrict_test(view_dict):
        return isinstance(view_dict['view'], target_classinfo)
    
    target_test = strict_test if strict else nonstrict_test
    
    endpoints = get_endpoints(api_tree)
    
    if not hasattr(catchall, 'catchall_custom_predicate'):
        def catchall_custom_predicate(context, request):
            return True
        
        catchall.catchall_custom_predicate = catchall_custom_predicate
    
    for complete_route, view_dicts_list in endpoints.items():
        if target_classinfo is not None:
            if not isinstance(target_classinfo, tuple):
                target_classinfo = (target_classinfo, )
            if not any(map(target_test, view_dicts_list)):
                continue
        
        catchall_kwargs = get_catchall_kwargs(
            catchall, view_dicts_list, view_kwargs, additional_view_kwargs
            )
        
        catchall_kwargs.update(additional_view_kwargs)
        
        configurator.add_view(
            route_name=complete_route,
            view=catchall,
            **catchall_kwargs
            )
    
    






