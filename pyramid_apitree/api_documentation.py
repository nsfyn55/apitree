""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """
import json
from iomanager import ListOf

INDENT_STR = '    '

class APIDocumentationView(object):
    @staticmethod
    def indent(s):
        return '\n'.join([INDENT_STR + line for line in s.splitlines()])
    
    def prepare_item(self, value):
        if isinstance(value, (list, tuple)):
            return self.prepare_list(value)
        if isinstance(value, dict):
            return self.prepare_dict(value)
        if isinstance(value, ListOf):
            return self.prepare_listof(value)
        
        return value.__name__
    
    def prepare_list(self, value):
        start, end = '[]'
        prepared_lines = map(self.prepare_item, value)
        all_lines = [start] + map(self.indent, prepared_lines) + [end]
        
        return '\n'.join(all_lines)
    
    def prepare_dict(self, value):
        start, end = '{}'
        prepared_lines = [
            "{}: {}".format(ikey, self.prepare_item(ivalue))
            for ikey, ivalue in value.iteritems()
            ]
        all_lines = [start] + map(self.indent, prepared_lines) + [end]
        
        return '\n'.join(all_lines)
    
    def prepare_listof(self, value):
        start, end = 'ListOf(', ')'
        
        iospec_obj = value.iospec_obj
        if not isinstance(iospec_obj, (list, dict)):
            joiner = ''
            wrapped = self.prepare_item(iospec_obj)
        else:
            joiner = '\n'
            wrapped = self.indent(self.prepare_item(iospec_obj))
        
        return joiner.join([start, wrapped, end])







