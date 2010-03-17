from datetime import datetime, date
from django.forms.forms import pretty_name
from django.utils.safestring import SafeUnicode
from django.template import defaultfilters
from django.forms.models import fields_for_model
from ..template.templatetags import general_formatter

class DataTable(object):
    WIDGET_COL = u'<th class="{sorter:false}">' #width="1", can't nowrap the columns below the header for widgets
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

    def render(self, queryset, fields=None, group=None, filter=None, add_sort=False, stop_at=None, header=True, footer=False, listfield_callback=None, row_callback=lambda obj: u'<tr>'):
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
        
        self.columns = DataTable.expand_fields(queryset, fields)
        
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
        heading = pretty_name(label) if label is not None else ''
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
                value = self.listfield_callback[key](key, obj, self.context)
            if column_index in self.listfield_callback:
                value = self.listfield_callback[column_index](key, obj, self.context)
        
        #Standard fetching
        if value is None:
            value = getattr(obj, key)
            if callable(value):
                value = value()

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
    def expand_fields(queryset, fields=None):
        if fields is None:
            fields = fields_for_model(queryset.model).keys()
    
        #Turn all columns into a list of (field, name)
        #:TODO: can fields exist as a dict instead of a list of two-tuples?
        columns = []
        for f in fields:
            if isinstance(f, tuple):
                columns.append(f)
            else:
                columns.append((f,f)) #Synthesize tuple
        return columns
        
