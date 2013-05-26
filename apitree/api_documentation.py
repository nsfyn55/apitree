""" Copyright (c) 2013 Josh Matthias <python.apitree@gmail.com> """
import inspect
import json
import os.path
from collections.abc import(
    Sequence,
    Mapping,
    )
from mako.template import Template
from iomanager import ListOf
from iomanager.iomanager import NotProvided
from pyramid.response import Response

from . import tree_scan
from .view_callable import SimpleViewCallable
from .tree_scan import (
    ALL_REQUEST_METHOD_STRINGS,
    get_endpoints,
    )
from .util import is_container

INDENT_STR = '    '

class Error(Exception):
    """ Base class for errors. """

class PreparationFailureError(Error):
    """ A value failed to coerce to a string via the 'prepare' method. """

class APIDocumentationMaker(object):
    documentation_view_class = SimpleViewCallable
    
    def __init__(self, api_tree={}, title='API Documentation'):
        self.documentation_dict = self.create_documentation(api_tree)
        self.documentation_title = title
        
        template_filename = os.path.join(
            os.path.dirname(__file__),
            'api_doc_template.mako',
            )
        
        self.documentation_html = Template(
            filename=template_filename,
            ).render(
            documentation_dict=self.documentation_dict,
            documentation_title = self.documentation_title,
            )
    
    def __call__(self, request):
        return self.documentation_html
    
    @staticmethod
    def indent(s):
        return '\n'.join([INDENT_STR + line for line in s.splitlines()])
    
    def prepare(self, value):
        if is_container(value, Sequence):
            return self.prepare_list(value)
        if isinstance(value, Mapping):
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
        prepared_lines = list(map(self.prepare, value))
        all_lines = [start] + list(map(self.indent, prepared_lines)) + [end]
        
        return '\n'.join(all_lines)
    
    def prepare_dict(self, value):
        start, end = '{}'
        prepared_lines = [
            "{}: {}".format(ikey, self.prepare(ivalue))
            for ikey, ivalue in value.items()
            ]
        all_lines = [start] + list(map(self.indent, prepared_lines)) + [end]
        
        return '\n'.join(all_lines)
    
    def prepare_listof(self, value):
        start, end = 'ListOf(', ')'
        
        iospec_obj = value.iospec_obj
        if is_container(iospec_obj, (Sequence, Mapping, ListOf)):
            joiner = '\n'
            wrapped = self.indent(self.prepare(iospec_obj))
        else:
            joiner = ''
            wrapped = self.prepare(iospec_obj)
        
        return joiner.join([start, wrapped, end])
    
    def get_keys_to_skip(self, view_callable):
        if not hasattr(view_callable, 'special_kwargs'):
            return []
        
        try:
            special_kwargs_dict = view_callable.special_kwargs()
        except Exception as exc:
            error_msg = (
                "ViewCallable 'special_kwargs' methods must not raise any "
                "exceptions when 'APIDocumentationMaker' is used."
            )
            exc.args = (error_msg, ) + exc.args
            raise
        
        return special_kwargs_dict.keys()
    
    def create_documentation(self, api_tree):
        endpoints = get_endpoints(api_tree)
        
        types_to_skip = getattr(self, 'types_to_skip', [])
        
        result = {}
        for path, endpoint_list in endpoints.items():
            path_methods = {}
            for item in endpoint_list:
                request_methods = item.get(
                    'request_method',
                    ALL_REQUEST_METHOD_STRINGS,
                    )
                method_key = ', '.join(request_methods)
                
                view_callable = item['view']
                if type(view_callable) in types_to_skip:
                    continue
                
                keys_to_skip = self.get_keys_to_skip(view_callable)
                
                method_dict = {}
                
                method_dict['description'] = (
                    view_callable.wrapped.__doc__ or 'No description provided.'
                    )
                
                if hasattr(view_callable, 'manager'):
                    manager = view_callable.manager
                    
                    raw_iospecs = {
                        'required': manager.input_processor.required.copy(),
                        'optional': manager.input_processor.optional.copy(),
                        'returns': manager.output_processor.required,
                        }
                    
                    for ikey_a in keys_to_skip:
                        for ikey_b in ['required', 'optional']:
                            raw_iospecs[ikey_b].pop(ikey_a, None)
                    
                    prepared_iospecs = {
                        ikey: self.prepare(ivalue)
                        for ikey, ivalue in raw_iospecs.items()
                        if ivalue is not NotProvided and ivalue != {}
                        }
                    
                    if manager.input_processor.unlimited:
                        prepared_iospecs['unlimited'] = (
                            manager.input_processor.unlimited
                            )
                    
                    method_dict.update(prepared_iospecs)
                
                path_methods[method_key] = method_dict
            
            if path_methods:
                result[path] = path_methods
        
        return result
    
    @classmethod
    def add_documentation_views(
        cls,
        configurator,
        api_tree,
        path='/api_docs',
        **view_kwargs
        ):
        api_docs = cls(api_tree)
        
        view_callable_class = cls.documentation_view_class
        
        view_kwargs.setdefault('request_method', 'GET')
        
        html_view_kwargs = {
            'accept': ''
            }
        html_view_kwargs.update(view_kwargs)
        
        json_view_kwargs = {
            'accept': 'application/json',
            'renderer': 'json'
            }
        json_view_kwargs.update(view_kwargs)
        
        @view_callable_class(**html_view_kwargs)
        def html_view(request):
            return Response(
                body=api_docs.documentation_html,
                content_type='text/html',
                status=200,
                )
        
        @view_callable_class(**json_view_kwargs)
        def json_view(request):
            return api_docs.documentation_dict
        
        configurator.add_route(name=path, pattern=path)
        
        for iview in [html_view, json_view]:
            configurator.add_view(
                route_name=path,
                view=iview,
                **iview.view_kwargs
                )







