""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

from pyramid_apitree.exc import BadAPITreeError

ALL_REQUEST_METHODS = ('GET', 'POST', 'PUT', 'DELETE', 'HEAD')

def get_endpoints(api_tree, root_path=''):
    """ Returns a dictionary, like this:
        {
            'complete/route': [
                {
                    'view': view_callable,
                    <More view_kwargs> ...
                    },
                <One 'view callable' dictionary for each request method.> ...
                ]
            }
        
        """
    
    endpoints = {}
    
    for ikey, ivalue in api_tree.iteritems():
        view_dict = {}
        
        if isinstance(ikey, tuple) or ikey in ALL_REQUEST_METHODS:
            view_dict['request_method'] = ikey
            branch_path = ''
        else:
            branch_path = ikey
        
        complete_route = root_path + branch_path
        
        if isinstance(ivalue, dict):
            endpoints.update(get_endpoints(ivalue, complete_route))
            continue
        
        view_callable = ivalue
        view_dict['view'] = view_callable
        
        if hasattr(view_callable, 'view_kwargs'):
            view_dict.update(view_callable.view_kwargs)
        
        view_dicts_list = endpoints.setdefault(complete_route, list())
        view_dicts_list.append(view_dict)
    
    return endpoints

def scan_api_tree(configurator, api_tree, root_path=''):
    endpoints = get_endpoints(api_tree, root_path=root_path)
    
    for complete_route, view_dicts_list in endpoints.iteritems():
        for view_dict in view_dicts_list:
            configurator.add_route(name=complete_route, pattern=complete_route)
            
            configurator.add_view(
                route_name=complete_route,
                **view_dict
                )






