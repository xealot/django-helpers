from datetime import datetime, date
from django.forms.forms import pretty_name
from django.utils.safestring import SafeUnicode
from django.template import defaultfilters
from helpers.templates import display_attribute
from helpers.utilities import get_query_string
from django.forms.models import fields_for_model


class DataTable(object):
    WIDGET_COL = u'<th class="{sorter:false}">' #width="1", can't nowrap the columns below the header for widgets
    REGULAR_COL = u'<th>'
    
    def __init__(self, wrapper=True, classes=()):
        self.output = []
        self.wrapper = wrapper
        self.classes = classes
        self.last_value = None

    def flush(self):
        return SafeUnicode(''.join(self.output))

    def writer(self, *texts):
        self.output.extend([SafeUnicode(t) for t in texts])

    def open_wrapper(self, classes, **kwargs):
        self.writer(u'<table class="', ' '.join(classes), u'" style="width:100%;">')

    def close_wrapper(self, **kwargs):
        self.writer(u'</table>')

    def render(self, queryset, fields=None, group=None, filter=None, row_filter=None, add_sort=False, stop_at=None, header=True, footer=False, listfield_callback=None):
        self.fields = fields
        self.group = group
        self.filter = filter
        self.row_filter = row_filter
        self.add_sort = add_sort
        self.header = header
        self.footer = footer
        self.listfield_callback = listfield_callback
        
        if self.wrapper:
            self.open_wrapper(self.classes)
        
        self.stop_at = int(stop_at) if stop_at is not None else None
        self.row = 0
    
        if fields is None:
            fields = fields_for_model(queryset.model).keys()
    
        #Turn all columns into a list of (field, name)
        #:TODO: can fields exist as a dict instead of a list of two-tuples?
        self.columns = []
        for f in fields:
            if isinstance(f, tuple):
                self.columns.append(f)
            else:
                self.columns.append((f,f)) #Synthesize tuple
        
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
                
                #Custom Row handler
                if row_filter is not None and hasattr(self.caller, row_filter):
                    self.writer(getattr(caller, row_filter(obj)))
                else:
                    self.writer(u'<tr>')
    
                #Render each column
                column_index = 1
                for key, label in self.columns:
                    self.render_column(obj, key, label, column_index)
                    column_index += 1
                self.writer(u'</tr>')
                
                #Stop for stop_at
                if stop_at and row >= stop_at:
                    break
        else:
            self.writer(u'<tr><td colspan="', len(columns), u'">There are no entries</td></tr>')
        self.writer(u'</tbody>')

        if self.should_render_footer():
            self.render_footer(context, columns)

        if self.wrapper:
            self.close_wrapper()
    
    def should_render_header(self):
        return self.header

    def should_render_footer(self):
        return self.footer

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
    
    def render_footer(self, columns):
        #Can I do this in the main function to start with, or is context more important
        c = context.kwargs
        qs = c['request'].GET
        params = context.get('parameters', None)
        params['colspan'] = len(columns)
        params['qs_last'] = get_query_string(qs, {'page': -1})
        params['qs_first'] = get_query_string(qs, {'page': 1})
        params['qs_next'] = get_query_string(qs, {'page': params['next_page']})
        params['qs_prev'] = get_query_string(qs, {'page': params['prev_page']})
        params['qs_limit_25'] = get_query_string(qs, {'limit': 25})
        params['qs_limit_50'] = get_query_string(qs, {'limit': 50})
        params['qs_limit_100'] = get_query_string(qs, {'limit': 100})
        self.writer(u"""
        <tfoot id="ajaxPager">
            <tr class="frow pager">
                <td colspan="%(colspan)s">
                    <div style="width: 33%%; float:left;">
                        Records: <span id="ajaxRecordFrom">%(start)s</span> to <span id="ajaxRecordTo">%(end)s</span> of <span id="ajaxRecords">%(query_size)s</span>
                    </div>
                    <div style="width: 33%%; float:left; text-align: center;">
                        <a href="%(qs_first)s" rel="history" class="table_first">First</a>
                        <a href="%(qs_prev)s" rel="history" class="table_prev">Prev</a>
                        Page <input type="text" style="width: 20px;" id="ajaxPageNo" value="%(page)s"/> of <span id="ajaxPages">%(pages)s</span>  
                        <a href="%(qs_next)s" rel="history" class="table_next">Next</a>
                        <a href="%(qs_last)s" rel="history" class="table_last">Last</a>
                    </div>
                    <div style="width: 33%%; float:left; text-align: right;">
                        Show 
                        <a href="%(qs_limit_25)s" rel="history" class="ajaxChangeLimit">25</a>/
                        <a href="%(qs_limit_50)s" rel="history" class="ajaxChangeLimit">50</a>/
                        <a href="%(qs_limit_100)s" rel="history" class="ajaxChangeLimit">100</a>
                        Records
                    </div>
                </td>
            </tr>
        </tfoot>""" % params)
    
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
        #:TODO: this function could use a lot of optimization in the form of returning early and saving checks to variables.
        #listfield callback handling
        if self.listfield_callback:
            if key in self.listfield_callback:
                return self.listfield_callback[key](key, obj)
            if column_index in self.listfield_callback:
                return self.listfield_callback[column_index](key, obj)
        
        #:TODO: depcreate:: DO NOT FILTER this through ANY function 
        if filter is False:
            val = getattr(obj, key)
            if callable(val):
                return val()
            return val
    
        #Default
        return display_attribute({}, obj, key, max_length=65, if_none="--")

    def render_column(self, obj, key, label, column_index):
        self.writer(u'<td>')
        self.writer(self.get_column_value(obj, key, label, column_index))
        self.writer(u'</td>')
