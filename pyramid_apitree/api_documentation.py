""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """
import inspect
import json
from iomanager import ListOf
from iomanager.iomanager import NotProvided

from .tree_scan import (
    ALL_REQUEST_METHODS,
    get_endpoints,
    )

INDENT_STR = '    '

class Error(Exception):
    """ Base class for errors. """

class PreparationFailureError(Error):
    """ A value failed to coerce to a string via the 'prepare' method. """

class APIDocumentationMaker(object):
    def __init__(self, api_tree={}):
        self.documentation_tree = self.create_documentation(api_tree)
    
    def __call__(self, request):
        return self.documentation_tree
    
    @staticmethod
    def indent(s):
        return '\n'.join([INDENT_STR + line for line in s.splitlines()])
    
    def prepare(self, value):
        if isinstance(value, (list, tuple)):
            return self.prepare_list(value)
        if isinstance(value, dict):
            return self.prepare_dict(value)
        if isinstance(value, ListOf):
            return self.prepare_listof(value)
        
        display_names = getattr(self, 'display_names', {})
        try:
            return display_names[value]
        except KeyError:
            return value.__name__
    
    def prepare_list(self, value):
        start, end = '[]'
        prepared_lines = map(self.prepare, value)
        all_lines = [start] + map(self.indent, prepared_lines) + [end]
        
        return '\n'.join(all_lines)
    
    def prepare_dict(self, value):
        start, end = '{}'
        prepared_lines = [
            "{}: {}".format(ikey, self.prepare(ivalue))
            for ikey, ivalue in value.iteritems()
            ]
        all_lines = [start] + map(self.indent, prepared_lines) + [end]
        
        return '\n'.join(all_lines)
    
    def prepare_listof(self, value):
        start, end = 'ListOf(', ')'
        
        iospec_obj = value.iospec_obj
        if not isinstance(iospec_obj, (list, dict)):
            joiner = ''
            wrapped = self.prepare(iospec_obj)
        else:
            joiner = '\n'
            wrapped = self.indent(self.prepare(iospec_obj))
        
        return joiner.join([start, wrapped, end])
    
    def create_documentation(self, api_tree):
        endpoints = get_endpoints(api_tree)
        
        types_to_skip = getattr(self, 'types_to_skip', [])
        
        result = {}
        for path, endpoint_list in endpoints.iteritems():
            path_methods = {}
            for item in endpoint_list:
                request_methods = item.get(
                    'request_method',
                    ALL_REQUEST_METHODS,
                    )
                method_key = ', '.join(request_methods)
                
                view_callable = item['view']
                if type(view_callable) in types_to_skip:
                    continue
                
                description = (
                    view_callable.__doc__ or 'No description provided.'
                    )
                
                manager = view_callable.manager
                iospecs = {
                    'required': manager.input_processor.required,
                    'optional': manager.input_processor.optional,
                    'returns': manager.output_processor.required,
                    }
                if manager.input_processor.unlimited:
                    iospecs['unlimited'] = manager.input_processor.unlimited
                method_dict = {
                    ikey: ivalue for ikey, ivalue in iospecs.iteritems()
                    if ivalue is not NotProvided and ivalue != {}
                    }
                
                method_dict['description'] = description
                
                path_methods[method_key] = method_dict
            
            if path_methods:
                result[path] = path_methods
        
        return result
    
    @classmethod
    def scan_and_insert(cls, api_tree, path, view_class, **kwargs):
        documentation_callable = cls(api_tree)
        view_callable = view_class(documentation_callable, **kwargs)
        api_tree.setdefault(path, {})
        api_tree[path]['GET'] = view_callable







