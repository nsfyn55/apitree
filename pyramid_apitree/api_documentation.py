""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """
import inspect
import json
from iomanager import ListOf

INDENT_STR = '    '

class Error(Exception):
    """ Base class for errors. """

class PreparationFailureError(Error):
    """ A value failed to coerce to a string via the 'prepare' method. """

class APIDocumentationView(object):
    @staticmethod
    def indent(s):
        return '\n'.join([INDENT_STR + line for line in s.splitlines()])
    
    def prepare(self, value):
        transformations = getattr(self, 'transformations', {})
        try:
            transformation = transformations[value]
        except (KeyError, TypeError):
            transformation = self.transform
        
        if callable(transformation):
            value = transformation(value)
        else:
            value = transformation
        
        if inspect.isclass(value):
            return value.__name__
        if isinstance(value, (list, tuple)):
            return self.prepare_list(value)
        if isinstance(value, dict):
            return self.prepare_dict(value)
        if isinstance(value, ListOf):
            return self.prepare_listof(value)
        
        if not isinstance(value, basestring):
            raise PreparationFailureError(
                "Result must be an 'str' or 'unicode' value; got a {}."
                .format(type(value).__name__)
                )
        
        return value
    
    def transform(self, value):
        return value
    
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







