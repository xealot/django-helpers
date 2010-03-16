from datetime import date, datetime
from django.forms.forms import pretty_name
from django.forms.models import fields_for_model
from django.utils.safestring import SafeUnicode
from mako import runtime
from base import DataTable

from ..utilities import get_query_string

def table(context, classes=(), record_url=None, instance=None, **kwargs):
    if not classes:
        classes = ['zebra', 'records', 'paging']
    if record_url is not None:
        classes.append(u"{record_url: '%s'}" % record_url)
    # id="pageTable" for ajax
    if not instance:
        instance = DataTableMako(classes=classes)
    instance.render(context, **kwargs)
    return instance.flush()


class DataTableMako(DataTable):
    def render(self, context, queryset, fields=None, group=None, filter=None, row_filter=None, add_sort=False, stop_at=None, header=True, footer=False, listfield_callback=None, row_callback=lambda obj: u'<tr>', **kwargs):
        context.caller_stack._push_frame()
        self.context = context
        self.caller = context.get('caller', runtime.UNDEFINED)
        self.capture = context.get('capture', runtime.UNDEFINED)

        if fields is runtime.UNDEFINED:
            fields = None
        if listfield_callback is None:
            listfield_callback = {}

        #Custom Row handler
        if row_filter is not None and hasattr(self.caller, row_filter):
            row_callback = getattr(self.caller, row_filter)
            #self.writer(getattr(self.caller, row_filter(obj)))

        #:TODO: this should be cache as to not re-run in the super class
        #Create listfield callback out of mako specfic variables
        columns = DataTableMako.expand_fields(queryset, fields)
        for key,label in columns:
            #FIRST COLUMN SPECIAL CASE ***DEPRECATED***
            if (key, label) == columns[0] and hasattr(self.caller, 'td__first'): #First column override :TODO: make this more generic
                #:TODO: I wish I didn't need to wrap this in a lambda, backward compat issue; also I don't know how passing context to a mako function works.
                listfield_callback[1] = lambda attr, obj, context: getattr(self.caller, 'td__first')(attr, obj)
            #:TODO: can we deprecate this too?
            if hasattr(self.caller, 'td_%s' % key):
                #:TODO: I wish I didn't need to wrap this in a lambda, backward compat issue; also I don't know how passing context to a mako function works.
                listfield_callback[key] = lambda attr, obj, context: getattr(self.caller, 'td_%s' % attr)(obj)
        
        try:
            super(DataTableMako, self).render(queryset, fields, group, filter, add_sort, stop_at, header, footer, listfield_callback, row_callback, **kwargs)
        finally:
            context.caller_stack._pop_frame()

    def get_group_value(self, obj):
        if hasattr(self.caller, 'td_%s' % self.group):
            value = getattr(self.caller, 'td_%s' % self.group)(obj)
        return super(DataTableMako, self).get_group_value(obj)

    def get_group_render_value(self, obj, value):
        if hasattr(self.caller, 'td_group'):
            return self.writer(getattr(self.caller, 'td_group')(obj))
        return super(DataTableMako, self).get_group_render_value(obj, value)

    def render_header(self, field, label):
        if hasattr(self.caller, 'th_%s' % label):
            self.writer(self.capture(getattr(self.caller, 'th_%s' % label)))
        else:
            super(DataTableMako, self).render_header(field, label)

    def get_column_value(self, obj, key, label, column_index):
        #:TODO: is this even used? Deprecate... :: Filter this through specified function
        if self.filter is not None and hasattr(self.caller, self.filter):
            return self.capture(getattr(self.caller, self.filter), obj, key)
        
        return super(DataTableMako, self).get_column_value(obj, key, label, column_index)

    def render_footer(self):
        #Can I do this in the main function to start with, or is context more important
        c = self.context.kwargs
        qs = c['request'].GET
        params = self.context.get('parameters', None)
        params['colspan'] = len(self.columns)
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
    
