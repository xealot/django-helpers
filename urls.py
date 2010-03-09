from django.conf.urls.defaults import *
import sys, inspect

def is_mod_function(mod, func):
    return inspect.isfunction(func) and inspect.getmodule(func) == mod

def list_functions(mod):
    return [func.__name__ for func in mod.__dict__.itervalues() if is_mod_function(mod, func)]

def lazy_url_patterns(module, pre_path=None):
    view_names = list_functions(module)
    views = dict([(x, getattr(module, x)) for x in view_names])
    view_args = {}
    urls = []
    for name, view in views.items():
        tmp_urls = []
        
        if pre_path:
            if name == 'index':
                url_regex = r'^%s/' % (pre_path)
            else:
                url_regex = r'^%s/%s/' % (pre_path, name)
            url_name_arg = '%s_%s' % (pre_path, name)
        else:
            if name == 'index':
                url_regex = r'^'
            else:
                url_regex = r'^%s/' % name
            url_name_arg = name

        argspec = inspect.getargspec(view)
        # Trim off the request argument that every view must have, and deal with defaults.
        args_without_defaults = []
        args_with_defaults = []
        if argspec[3]:
            args_with_defaults = argspec[0][len(argspec[0]) - len(argspec[3]):]
            args_without_defaults = argspec[0][1:len(argspec[0]) - len(argspec[3])]
        else:
            args_without_defaults = argspec[0][1:]
        for arg in args_without_defaults:
            url_regex += '(?P<%s>.*)/' % arg
        tmp_urls.append(url(url_regex + '$', view, name=url_name_arg))
        
        for default_arg in args_with_defaults:
            url_regex += '(?P<%s>.*)/' % default_arg
            url_name_arg += '_' + default_arg
            tmp_urls.append(url(url_regex + '$', view, name=url_name_arg))
        tmp_urls.reverse()
        urls.extend(tmp_urls)
    return urls
