""" Copyright (c) 2013 Josh Matthias <python.apitree@gmail.com> """

from .api_documentation import APIDocumentationMaker
from .tree_scan import (
    scan_api_tree,
    add_catchall,
    RequestMethod,
    GET,
    POST,
    PUT,
    DELETE,
    HEAD,
    )
from .view_callable import (
    BaseViewCallable,
    SimpleViewCallable,
    FunctionViewCallable,
    APIViewCallable,
    )

# Lowercase decorator names - an aesthetic choice.
simple_view = SimpleViewCallable
function_view = FunctionViewCallable
api_view = APIViewCallable