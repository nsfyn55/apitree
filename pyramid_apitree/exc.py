""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

class Error(Exception):
    """ Base class for errors. """

class BadAPITreeError(Error):
    """ API tree has invalid structure or composition. """

class BadAPITreeStructureError(BadAPITreeError):
    """ API tree could not be traversed. An API tree must be either a dictionary
        or a list of 2-length tuples. """