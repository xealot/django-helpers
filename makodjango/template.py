from mako.template import Template as MakoTemplate
from mako import exceptions
from django.conf import settings
from django.http import HttpResponse
import traceback, sys

class Template(object):
    def __init__(self, template_object):
        self.template = template_object

    def render(self, context):
        context_dict = {}
        for d in context.dicts:
            context_dict.update(d)

        try:
            return self.template.render(attributes={}, **context_dict)
        except:
            print '\n'.join(traceback.format_exception(*(sys.exc_info())))
            if settings.DEBUG:
                return HttpResponse(exceptions.html_error_template().render())
            raise

def get_template_from_string(source, origin=None, name=None):
    """
    Returns a compiled Template object for the given template code,
    handling template inheritance recursively.
    """
    return MakoTemplate(source)