""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

from pyramid_apitree.exc import BadAPITreeError

ALL_REQUEST_METHODS = ('GET', 'POST', 'PUT', 'DELETE', 'HEAD')

def get_endpoints(api_tree, root_path=''):
    """ Returns a dictionary, like this:
        {
            'complete/route': {
                'view': view_callable,
                <more view_kwargs> ...
                }
            } """
    
    endpoints = {}
    
    for ikey, ivalue in api_tree.iteritems():
        endpoint_dict = {}
        
        if isinstance(ikey, tuple):
            endpoint_dict['request_methods'] = ikey
            branch_path = ''
        elif ikey in ALL_REQUEST_METHODS:
            endpoint_dict['request_methods'] = (ikey, )
            branch_path = ''
        else:
            branch_path = ikey
        
        complete_route = root_path + branch_path
        
        if isinstance(ivalue, dict):
            endpoints.update(get_endpoints(ivalue, complete_route))
            continue
        
        endpoint_dict['view'] = ivalue
        
        endpoints[complete_route] = endpoint_dict
    
    return endpoints

def scan_api_tree(configurator, api_tree, root_path=''):
    endpoints = get_endpoints(api_tree, root_path=root_path)
    
    for complete_route, view_dict in endpoints.iteritems():
        configurator.add_route(name=complete_route, pattern=complete_route)
        
        configurator.add_view(
            route_name=complete_route,
            **view_dict
            )







