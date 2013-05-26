""" Copyright (c) 2013 Josh Matthias <python.apitree@gmail.com> """

class Error(Exception):
    """ Base class for errors. """

class APITreeError(Error):
    """ API tree has invalid structure or composition. """

class APITreeStructureError(APITreeError):
    """ API tree could not be traversed. An API tree must be either a dictionary
        or a list of 2-length tuples. """