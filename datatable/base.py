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

    def flush(self):
        return SafeUnicode(''.join(self.output))

    def writer(self, *texts):
        self.output.extend([SafeUnicode(t) for t in texts])

    def open_wrapper(self, classes, **kwargs):
        self.writer(u'<table class="', ' '.join(classes), u'" style="width:100%;">')

    def close_wrapper(self, **kwargs):
        self.writer(u'</table>')

    def render(self, queryset, fields=None, group=None, filter=None, row_filter=None, add_sort=False, stop_at=None, header=True, cap=None, footer=False, listfield_callback=None, **kwargs):
        if self.wrapper:
            self.open_wrapper(self.classes)
        
        row = 0
        stop_at = int(stop_at) if stop_at is not None else None
    
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
        
        #Table Header
        if self.should_render_header(**dict([x for x in locals().items() if x[0] != 'self'])):
            self.render_headers(columns, add_sort=False, cap=False)
    
        #Table Body
        self.writer(u'<tbody>')
        if queryset:
            last_value = None
            
            for obj in queryset:
                row += 1
                #Handle group by rendering
                if group:
                    last_value = self.attempt_group(group, obj, columns, last_value)
                
                #Custom Row handler
                if row_filter is not None and hasattr(self.caller, row_filter):
                    self.writer(getattr(caller, row_filter(obj)))
                else:
                    self.writer(u'<tr>')
    
                #Render each column
                column_index = 1
                for key, label in columns:
                    self.render_column(obj, key, label, columns, column_index, filter, listfield_callback, **kwargs)
                    column_index += 1
                if cap is not None:
                    self.writer(u'<td style="white-space:nowrap;">', getattr(caller, cap)(obj), u'</td>')
                self.writer(u'</tr>')
                
                #Stop for stop_at
                if stop_at and row >= stop_at:
                    break
        else:
            self.writer(u'<tr><td colspan="', len(columns), u'">There are no entries</td></tr>')
        self.writer(u'</tbody>')

        if self.should_render_footer(**dict([x for x in locals().items() if x[0] != 'self'])):
            self.render_footer(context, columns)

        if self.wrapper:
            self.close_wrapper()
    
    def should_render_header(self, **kwargs):
        return header

    def should_render_footer(self, **kwargs):
        return footer

    def render_header(self, field, label, add_sort, cap):
        heading = pretty_name(label) if label is not None else ''
        th = self.REGULAR_COL if label is not None else self.WIDGET_COL
        if add_sort:
            self.writer(th, u'<a href="" class="ajaxSort" rel="', field, u'">', heading, u'</a>', u'</th>')
        else:
            self.writer(th, heading, u'</th>')
        
    def render_headers(self, columns, add_sort=False, cap=False):
        self.writer(u'<thead><tr class="hrow headers">')
        for field, label in columns:
            self.render_header(field, label, add_sort, cap)
        if cap is not False:
            self.writer(WIDGET_COL, u'</th>')
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
    
    def attempt_group(self, group, obj, columns, last_value=None):
        value = self.get_group_value(group, obj, columns)
        
        if last_value is None or value != last_value:
            self.render_group(group, obj, columns, value)
        return value
    
    def get_group_value(self, group, obj, columns):
        value = getattr(obj, group)
        if isinstance(value, (date, datetime)):
            value = defaultfilters.date(value)
        return value
    
    def get_group_render_value(self, group, obj, columns, value):
        return value

    def render_group(self, group, obj, columns, value):
        self.writer(u'<tr><td colspan="', len(columns), u'" class="tr_group">')
        self.writer(self.get_group_render_value(group, obj, columns, value))
        self.writer(u'</td></tr>')

    def get_column_value(self, obj, key, label, columns, column_index, filter, listfield_callback, **kwargs):
        #:TODO: this function could use a lot of optimization in the form of returning early and saving checks to variables.
        #listfield callback handling
        if listfield_callback:
            if key in listfield_callback:
                return listfield_callback[key](key, obj, context)
            if column_index in listfield_callback:
                return listfield_callback[column_index](key, obj, context)
        
        #:TODO: depcreate:: DO NOT FILTER this through ANY function 
        if filter is False:
            val = getattr(obj, key)
            if callable(val):
                return val()
            return val
    
        #Default
        return display_attribute({}, obj, key, max_length=65, if_none="--")

    def render_column(self, obj, key, label, columns, column_index, filter, listfield_callback, **kwargs):
        self.writer(u'<td>')
        self.writer(self.get_column_value(obj, key, label, columns, column_index, filter, listfield_callback, **kwargs))
        self.writer(u'</td>')
