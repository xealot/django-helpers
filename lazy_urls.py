from django.conf import settings
from django.conf.urls.defaults import url
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule
import inspect

def is_mod_function(mod, func):
    return inspect.isfunction(func) and inspect.getmodule(func) == mod

def list_functions(mod):
    return [func.__name__ for func in mod.__dict__.itervalues() if is_mod_function(mod, func)]

def lazy_urlpatterns(*args, **kwargs):
    empty_ok = kwargs.pop('_empty_ok', True)
    do_all = kwargs.pop('_all', False)
    patterns = []

    apps_done = []
    if len(args):
        for app_label in args:
            apps_done += [app_label]
            patterns.extend(lazy_urlpatterns_app(app_label, app_label, empty_ok))
    
    if len(kwargs):
        for app_label, pre_path in kwargs.items():
            apps_done += [app_label]
            patterns.extend(lazy_urlpatterns_app(app_label, pre_path, empty_ok))
    
    # Do all the unspecified patterns now.
    if do_all or (len(kwargs) == 0 and len(args) == 0):
        for app_name in settings.INSTALLED_APPS:
            if app_name not in apps_done:
                tmp_name = app_name.split('.')[-1]
                patterns.extend(lazy_urlpatterns_app(tmp_name, tmp_name, empty_ok))
    return patterns
    
def lazy_urlpatterns_app(app_label, pre_path=None, emptyOK=True):
    for app_name in settings.INSTALLED_APPS:
        if app_label == app_name.split('.')[-1]:
            app_module = import_module(app_name)
            try:
                view_module = import_module('.views', app_name)
            except ImportError:
                if emptyOK is True and not module_has_submodule(app_module, 'views'):
                    return []
                else:
                    raise
    
    view_names = list_functions(view_module)
    views = dict([(x, getattr(view_module, x)) for x in view_names])
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
