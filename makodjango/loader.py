from mako.lookup import TemplateLookup
from mako import exceptions
from django.template.loaders import filesystem
from django.conf import settings
from django.template import TemplateDoesNotExist
from helpers.makodjango.template import Template
import tempfile

directories      = getattr(settings, 'MAKO_TEMPLATE_DIRS', settings.TEMPLATE_DIRS)
module_directory = getattr(settings, 'MAKO_MODULE_DIR', None)
output_encoding  = getattr(settings, 'MAKO_OUTPUT_ENCODING', 'utf-8')
encoding_errors  = getattr(settings, 'MAKO_ENCODING_ERRORS', 'replace')

if module_directory is None:
    #We can't put this in the getattr default because it executes there, creating a bunch of empty dirs.
    module_directory = tempfile.mkdtemp()

lookup = TemplateLookup(directories=directories, 
                        module_directory=module_directory,
                        output_encoding=output_encoding, 
                        encoding_errors=encoding_errors,
                        collection_size=1000,
                        filesystem_checks=settings.DEBUG,)


class Loader(filesystem.Loader):
    is_usable = True
    def load_template(self, template_name, template_dirs=None):
        #origin should be full path, mako gives this I'm sure.
        try:
            template, origin = Template(lookup.get_template(template_name)), template_name
        except exceptions.TopLevelLookupException:
            raise TemplateDoesNotExist('Mako template not in mako directories')
        return template, origin
