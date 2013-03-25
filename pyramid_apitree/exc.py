class Error(Exception):
    """ Base class for errors. """

class BadAPITreeError(Error):
    """ Provided API tree dictionary has invalid structure or composition. """