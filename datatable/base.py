from datetime import datetime, date
from django.forms.forms import pretty_name
from django.utils.safestring import SafeUnicode, mark_safe
from django.template import defaultfilters
from django.forms.models import fields_for_model
from ..template.templatetags import general_formatter
from ..general import get_default_fields
from django.template.defaultfilters import slugify
from django.utils.encoding import force_unicode


from plugins import *

class MissingPluginRequirementError(Exception): pass
class CallChain(object):
    """Type for keeping up with chain variable and adding pre and post elements"""
    def __init__(self, instance, initial, chain=None, *a, **kw):
        chain = chain or initial
        self.instance, self.initial, self.chain, self.prefix, self.suffix = instance, initial, chain, [], []
        
    def pre(self, *args):
        self.prefix.extend(args)

    def post(self, *args):
        self.suffix.extend(args)
        
    def get_list(self):
        return self.prefix + [self.chain] + self.suffix


class BaseTable(object):
    def __init__(self, include_header=True, include_body=True, include_footer=True, plugins=()):
        self.include_header, self.include_body, self.include_footer = include_header, include_body, include_footer
        self._plugin_classes = []
        self._plugins = []
        for plugin in plugins:
            self.add_plugin(plugin)

    def build(self, data, columns=(), exclude=()):
        """Accepts any iterable with subscriptable access"""
        element_list = []

        #Process Headers
        columns = self.prepare_columns(data, columns, exclude)
        if self.include_header:
            hdrs = self.build_headers(data, columns)
            if hdrs is not None:
                element_list.extend(self.head(hdrs))

        if self.include_body:
            element_list.extend(self.body(self.build_body(data, columns))) #Process Body

        #Optional Footer
        if self.include_footer:
            ftrs = self.build_footer(data)
            if ftrs is not None:
                element_list.extend(self.footer(ftrs))

        return self.finalize(element_list)[0]

    def build_footer(self, data):
        footer = self.footer(data)
        if data is footer[0]:
            return None
        return footer

    def output(self, data, columns=(), exclude=()):
        """Build and output data"""
        return self.build(data, columns, exclude)

    def add_plugin(self, plugin):
        plugin = callable(plugin) and plugin() or plugin
        plugin_class = plugin.__class__
        
        if hasattr(plugin_class, 'REQUIRES'):
            required = set(plugin_class.REQUIRES)
            installed = set(self._plugin_classes)
            if not installed.issuperset(required):
                raise MissingPluginRequirementError(','.join([str(p.__name__) for p in required.difference(installed)]))
        
        self._plugin_classes.append(plugin_class)
        self._plugins.append(plugin)

    def call_chain(self, method_name, value, *args, **kwargs):
        callchain = CallChain(self, value)
        for plugin in self._plugins:
            method = getattr(plugin, method_name, None)
            if method is not None and callable(method):
                new_value = method(callchain, *args, **kwargs)
                if new_value is not None:
                    callchain.chain = new_value
                #method(callchain, *args, **kwargs)
        return callchain.get_list()

    def head(self, value):
        """Called once before row iteration"""
        return self.call_chain('head', value)

    def header(self, value, column_index=None):
        """Called for every header"""
        return self.call_chain('header', value, column_index=None)

    def body(self, value):
        """Called once before row iteration"""
        return self.call_chain('body', value)
    
    def row(self, value, row_number=0):
        """Called for each row, always returns a list"""
        return self.call_chain('row', value, row_number)

    def cell(self, value, data=None, row_number=0, column_index=None):
        """Called on each piece of data added into the table"""
        return self.call_chain('cell', value, data, row_number, column_index)

    def footer(self, value):
        """Wrapping the foot calls"""
        return self.call_chain('footer', value)

    def foot(self, value):
        """Called on each piece of data added into the table"""
        return self.call_chain('foot', value)
    
    def finalize(self, value):
        """Close Table"""
        return self.call_chain('finalize', value)


class BaseDictTable(BaseTable):
    def build_headers(self, data, columns, exclude):
        headers = []
        for header in self.get_headers(data):
            headers.extend(self.header(header))
        return headers or None
    
    def get_headers(self, initial):
        if initial:
            return [(k, k) for k in initial[0].keys()]
        return ()
    
    def build_body(self, data):
        body_data, row_number = [], 0
        for row in data:
            row_number+=1
            cells = []
            for key, col in row.items():
                cells.extend(self.cell(col, data=row, row_number=row_number, column_index=key))
            try: 
                body_data.extend(self.row(cells, row_number=row_number))
            except StopIteration:
                break
        return body_data



#from lxml import etree        
#from lxml.html import builder as E
#from plugins import DTUnicode, DTHtmlTable, DTPluginBase

#bt = BaseDictTable(plugins=(DTUnicode, DTHtmlTable, DTSelectable))
#print etree.tostring(bt.output([{'one': 1, 'two': 2},{'one': 2, 'two': 3}]), method='xml', encoding=unicode, pretty_print=True)






















class DataTable(object):
    WIDGET_COL = u'<th class="{sorter:false}" width="1">'
    REGULAR_COL = u'<th>'
    
    def __init__(self, wrapper=True, classes=()):
        self.output = []
        self.wrapper = wrapper
        self.classes = classes
        self.last_value = None
        self.context = {} #Move to TemplateDataTable?

    def flush(self):
        return SafeUnicode(''.join(self.output))

    def writer(self, *texts):
        self.output.extend([SafeUnicode(t) for t in texts])

    def open_wrapper(self, classes, **kwargs):
        self.writer(u'<table class="', ' '.join(classes), u'" style="width:100%;">')

    def close_wrapper(self, **kwargs):
        self.writer(u'</table>')

    def render(self, queryset, fields=(), exclude=(), group=None, filter=None, add_sort=False, stop_at=None, header=True, footer=False, listfield_callback=None, row_callback=lambda obj: u'<tr>'):
        self.fields = fields
        self.group = group
        self.filter = filter
        self.add_sort = add_sort
        self.header = header
        self.footer = footer
        self.listfield_callback = listfield_callback
        
        if self.wrapper:
            self.open_wrapper(self.classes)
        
        self.stop_at = int(stop_at) if stop_at is not None else None
        self.row = 0

        self.columns = DataTable.expand_fields(queryset, fields, exclude)
        
        #Table Header
        if self.should_render_header():
            self.render_headers()
    
        #Table Body
        self.writer(u'<tbody>')
        if queryset:
            self.last_value = None
            
            for obj in queryset:
                self.row += 1
                #Handle group by rendering
                if self.should_render_group(obj):
                    self.render_group(obj, self.last_value)
                
                self.writer(row_callback(obj))
    
                #Render each column
                column_index = 1
                for key, label in self.columns:
                    self.render_column(obj, key, label, column_index)
                    column_index += 1
                self.writer(u'</tr>')
                
                #Stop for stop_at
                if stop_at and self.row >= stop_at:
                    break
        else:
            self.writer(u'<tr><td colspan="', len(self.columns), u'">There are no entries</td></tr>')
        self.writer(u'</tbody>')

        if self.should_render_footer():
            self.render_footer()

        if self.wrapper:
            self.close_wrapper()
    
    def should_render_header(self):
        return self.header

    def render_header(self, field, label):
        heading = label if label is not None else ''
        th = self.REGULAR_COL if label is not None else self.WIDGET_COL
        if self.add_sort:
            self.writer(th, u'<a href="" class="ajaxSort" rel="', field, u'">', heading, u'</a>', u'</th>')
        else:
            self.writer(th, heading, u'</th>')
        
    def render_headers(self):
        self.writer(u'<thead><tr class="hrow headers">')
        for field, label in self.columns:
            self.render_header(field, label)
        self.writer(u'</tr></thead>')
    
    def should_render_footer(self):
        return self.footer

    def render_footer(self):
        pass
    
    def should_render_group(self, obj):
        if not self.group:
            return False

        value = self.get_group_value(obj)
        
        if self.last_value is None or value != self.last_value:
            self.last_value = value
            return True
        return False
    
    def get_group_value(self, obj):
        if isinstance(obj, dict):
            value = obj[self.group]
        else:
            value = getattr(obj, self.group)
            
        if isinstance(value, (date, datetime)):
            value = defaultfilters.date(value)
        return value
    
    def get_group_render_value(self, obj, value):
        return value

    def render_group(self, obj, value):
        self.writer(u'<tr><td colspan="', len(self.columns), u'" class="tr_group">')
        self.writer(self.get_group_render_value(obj, value))
        self.writer(u'</td></tr>')

    def get_column_value(self, obj, key, label, column_index):
        value = None
        #Callback fetching
        if self.listfield_callback:
            if key in self.listfield_callback:
                value = mark_safe(self.listfield_callback[key](key, obj, self.context))
            if column_index in self.listfield_callback:
                value = mark_safe(self.listfield_callback[column_index](key, obj, self.context))

        #Standard fetching
        if value is None:
            try:
                value = getattr(obj, key)
            except AttributeError:
                value = obj[key]
            custom_display_func = 'get_%s_display' % key
            if hasattr(obj, custom_display_func):
                value = getattr(obj, custom_display_func)
            if callable(value):
                value = value()
        value = force_unicode(value) #Needs to be unicode before filters

        #Now Filter
        if self.filter is None: #Standard sanity filter
            return general_formatter(value, max_length=65, if_none="--")
        elif callable(self.filter):
            return self.filter(obj, key)
        return value

    def render_column(self, obj, key, label, column_index):
        self.writer(u'<td>')
        self.writer(self.get_column_value(obj, key, label, column_index))
        self.writer(u'</td>')
    
    @staticmethod
    def expand_fields(queryset, fields=(), exclude=()):
        #:TODO: can fields exist as a dict instead of a list of two-tuples?
        if hasattr(queryset, 'model'):
            return get_default_fields(queryset.model, fields, exclude or None, include_verbose=True)
        
        #assume this is a dictionary
        if not fields:
            fields = queryset.keys()
        
        #Turn all columns into a list of (field, name)
        columns = []
        for f in fields:
            if f in exclude:
                continue
            if isinstance(f, tuple):
                columns.append(f)
            else:
                columns.append((f, f)) #Synthesize tuple
        return columns



class DataGrid(DataTable):
    def __init__(self, *args, **kwargs):
        super(DataGrid, self).__init__(*args, **kwargs)
        self.footer = True #Contains management form
        self.group = None
        self.filter = None
        self.add_sort = False
        self.stop_at = None

    def render(self, formset, fields=(), exclude=(), header=True, listfield_callback=None, row_callback=lambda obj: u'<tr>'):
        self.fields = fields 
        self.header = header
        self.listfield_callback = listfield_callback

        if self.wrapper:
            self.open_wrapper(self.classes)
        
        self.row = 0

        self.columns = self.expand_fields(formset, fields, exclude)

        #Table Header
        if self.should_render_header():
            self.render_headers()
    
        #Table Body
        self.writer(u'<tbody>')
        if formset.forms:
            for obj in formset.forms:
                self.row += 1
                
                #Errors
                if self.should_render_group(obj):
                    self.render_group(obj, self.last_value)
                    
                self.writer(row_callback(obj))
   
                #Render each column
                column_index = 1
                for key, label in self.columns:
                    self.render_column(obj, key, label, column_index)
                    column_index += 1
                self.writer(u'</tr>')
                
        else:
            self.writer(u'<tr><td colspan="', len(self.columns), u'">There are no entries</td></tr>')
        self.writer(u'</tbody>')

        if self.should_render_footer():
            self.render_footer(formset)

        if self.wrapper:
            self.close_wrapper()

    def render_header(self, field, label):
        heading = pretty_name(label) if label is not None else ''
        th = self.REGULAR_COL if field is not 'DELETE' else self.WIDGET_COL
        self.writer(th, heading, u'</th>')

    def render_footer(self, formset):
        self.writer(unicode(formset.management_form))

    def render_column(self, obj, key, label, column_index):
        bf = obj[key]
        self.writer(u'<td>', u'<div class="inputWrapper %s %s">' % (bf._auto_id(), bf.field.getCssClass()))
        if column_index == 1:
            self.writer(*[f.as_widget() for f in obj.hidden_fields()])
        self.writer(self.get_column_value(obj, key, label, column_index))
        self.writer(u'</div></td>')
        
    def get_column_value(self, obj, key, label, column_index):
        #:TODO: can we use render field here?
        bf = obj[key]
        return bf.as_widget()

    def expand_fields(self, formset, fields=(), exclude=()):
        if not fields:
            first_form = formset.forms[0]
            fields = [(f.name, f.label) for f in first_form.visible_fields()]

        #Turn all columns into a list of (field, name)
        columns = []
        for f in fields:
            if f in exclude:
                continue
            if isinstance(f, tuple):
                columns.append(f)
            else:
                columns.append((f,f)) #Synthesize tuple
        return columns

    def should_render_group(self, obj):
        if obj.errors:
            return True
        return False
    
    def render_group(self, obj, value):
        self.writer(u'<tr class="error_row"><td colspan="', len(self.columns), u'" class="tr_group">')
        self.writer(u'Please correct the errors in the row below.', obj.non_field_errors())
        self.writer(u'</td></tr>')
        
        self.writer(u'<tr class="error_row">')
        for field, label in self.columns:
            bf = obj[field]
            self.writer(u'<td>', bf.errors, u'</td>')
        self.writer(u'</tr>')
        
