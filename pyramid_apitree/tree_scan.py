""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

from pyramid_apitree.exc import BadAPITreeError

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
        
        complete_route = root_path + ikey
        
        if isinstance(ivalue, dict):
            endpoints.update(get_endpoints(ivalue, complete_route))
            continue
        
        endpoints[complete_route] = {'view': ivalue}
    
    return endpoints

def scan_api_tree(configurator, api_tree, root_path=''):
    endpoints = get_endpoints(api_tree, root_path=root_path)
    
    for complete_route, view_dict in endpoints.iteritems():
        configurator.add_route(name=complete_route, pattern=complete_route)
        
        configurator.add_view(
            route_name=complete_route,
            **view_dict
            )







