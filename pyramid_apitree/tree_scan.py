""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

from copy import deepcopy
from .exc import BadAPITreeError

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

GET, POST, PUT, DELETE, HEAD = \
ALL_REQUEST_METHODS = tuple(map(RequestMethod, ALL_REQUEST_METHOD_STRINGS))

def conglomerate_endpoints(endpoints_dicts_list):
    result = {}
    for endpoints_dict in endpoints_dicts_list:
        for ikey, ivalue in endpoints_dict.items():
            views_list = result.setdefault(ikey, list())
            views_list.extend(ivalue)
    return result

def parse_branch(branch_location, branch_obj, root_path):
    """ Return value has the same format as 'get_endpoints'. """
    if isinstance(branch_location, tuple):
        if all(
            [isinstance(item, RequestMethod) for item in branch_location]
            ):
            # branch_location is a tuple of request methods. Sum to a single
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
        raise BadAPITreeError(
            "Invalid branch route object. Must be one of: a string path "
            "component ('/something'); a RequestMethod instance; or a "
            "tuple of those. Got: {}"
            .format(type(branch_path).__name__)
            )
    
    if isinstance(branch_obj, dict):
        if request_method is not None:
            invalid_path = complete_route + '/' + str(request_method)
            raise BadAPITreeError(
                "RequestMethod-instance branch routes (GET, POST, etc.) "
                "cannot have a dictionary of sub-routes. Invalid path: {}"
                .format(invalid_path)
                )
        
        return get_endpoints(branch_obj, complete_route)
    
    # Branch contains a single view.
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
    
    result_list = [
        parse_branch(ikey, ivalue, root_path)
        for ikey, ivalue in api_tree.items()
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






