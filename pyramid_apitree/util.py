""" Copyright (c) 2013 Josh Matthias <python.apitree@gmail.com> """

def is_container(obj, classinfo):
    """ 'obj' is an instance of 'classinfo', but is not a 'str' or 'bytes'
        instance. """
    if isinstance(obj, classinfo) and not isinstance(obj, (str, bytes)):
        return True
    return False