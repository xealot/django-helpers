from urllib import urlencode
from cgi import escape

def partition(params, prefix=None):
    """
    Partition querystring variables based on a prefix for each key, 
    this is a great way to make sure you're only operating on a specific 
    subset of parameters.
    """
    prefixed, other = [], []
    for i, v in params.items():
        if prefix is not None and i.startswith(prefix):
            prefixed.append((str(i[len(prefix):]), v))
        else:
            other.append((str(i), v))
    return dict(prefixed), dict(other)

def morph(params, prefix=None, **kwargs):
    """
    This function will operate on an existing querystring to update, remove 
    or otherwise modify pieces of it without changing some or all of the rest of it.
    """
    p, p_all = partition(params, prefix)
    for k, v in kwargs.items():
        if v is None and k in p:
            del p[k]
        else:
            p[k] = v
    
    #Add prefix back to p and update p_all
    p_all.update(dict([((prefix or '')+i, v) for i, v in p.items()]))
    return '?%s' % escape(urlencode(p_all)) #escape is required for LXML parsing.