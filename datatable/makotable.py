from functools import partial
from django.core.urlresolvers import reverse
from django.utils.safestring import SafeUnicode
from mako import runtime
from base import DataTable, DataGrid

from ..utilities import get_query_string
from ..template.templatetags import display_attribute

from base import DTPluginBase
from djangotable import ModelTable
from plugins import xmlstring, DTGeneralFormatter, DTUnicode, DTHtmlTable, DTWrapper, DTSelectable, DTCallback


class NGLegacyCSS(DTPluginBase):
    REQUIRES = [DTHtmlTable]
    """This class adds javascript sorting to the table headers and tag."""
    def head(self, callchain, *args):
        self.add_class(callchain.chain, ['headers hrow'])



def table(context, queryset, fields=(), exclude=(), classes=(), record_url=None, instance=None, make_selectable=False, make_editable=False, listfield_callback=None, wrapper=True, **kwargs):
    listfield_callback = listfield_callback or {}

    #THe crazy mako shit is mostly at the top
    try:
        context.caller_stack._push_frame()
        caller = context.get('caller', runtime.UNDEFINED)
        capture = context.get('capture', runtime.UNDEFINED)

        for key in fields:
            index = isinstance(key, (tuple, list)) and key[0] or key
            #FIRST COLUMN SPECIAL CASE ***DEPRECATED***
            if key == fields[0] and hasattr(caller, 'td__first'): #First column override :TODO: make this more generic
                #:TODO: I wish I didn't need to wrap this in a lambda, backward compat issue; also I don't know how passing context to a mako function works.
                listfield_callback[1] = partial(capture, lambda attr, obj, context: getattr(caller, 'td__first')(attr, obj))
            #:TODO: can we deprecate this too?
            if hasattr(caller, 'td_%s' % index):
                func = getattr(caller, 'td_%s' % index)
                listfield_callback[key] = partial(capture, partial(lambda func, attr, obj: func(obj), func))
    finally:
        context.caller_stack._pop_frame()
    #End completely crazy mako shit

    plugins = [DTGeneralFormatter, DTUnicode, DTHtmlTable, NGLegacyCSS]
    #Give table appropriate CSS classes
    if listfield_callback:
        plugins.insert(2, DTCallback(listfield_callback))

    if not classes:
        classes = ['zebra', 'records', 'paging']
    if record_url is not None:
        classes = classes + [u"{record_url: '%s'}" % record_url]

    if wrapper is True:
        plugins.append(DTWrapper(classes=classes, style='width: 100%;'))
    if make_selectable is not False and make_selectable != runtime.UNDEFINED:
        plugins.append(DTSelectable(make_selectable))
    table = ModelTable(plugins=plugins, finalize=wrapper)
    return xmlstring(table.build(queryset, columns=fields, exclude=exclude))


def ajaxstub(context, queryset, record_url, fields=(), exclude=(), listfield_callback=None, make_selectable=False, linker=False, labeler=False):
    from ajax import stub
    request = context.get('request')
    params = context.get('qstats')
    return stub(queryset, params, record_url, fields, exclude, listfield_callback, make_selectable, linker, labeler)

def ajaxtable(context, queryset, fields=(), exclude=(), listfield_callback=None, make_selectable=False):
    from ajax import table
    request = context.get('request')
    return table(queryset, request.GET, fields, exclude, make_selectable, listfield_callback)








def table2(context, queryset, fields=(), exclude=(), classes=(), record_url=None, instance=None, make_selectable=False, make_editable=False, listfield_callback=None, wrapper=True, **kwargs):
    listfield_callback = listfield_callback or {}
    if not classes:
        classes = ['zebra', 'records', 'paging']
    if fields is runtime.UNDEFINED:
        fields = DataTableMako.expand_fields(queryset, fields, exclude)
    fields = list(fields)
    if record_url is not None:
        classes.append(u"{record_url: '%s'}" % record_url)

    if make_selectable is not False:
        classes.append(u'selectable')
        fields.insert(0, ('checkbox', None))
        if make_selectable is True:
            listfield_callback['checkbox'] = lambda attr, obj, context: '<input type="checkbox" name="selection" value="%s" />' % obj.pk
        else:
            if isinstance(queryset, list):
                listfield_callback['checkbox'] = lambda attr, obj, context: '<input type="checkbox" name="selection" value="%s" />' % obj[make_selectable]
            else:
                listfield_callback['checkbox'] = lambda attr, obj, context: '<input type="checkbox" name="selection" value="%s" />' % getattr(obj, make_selectable)

    if make_editable is not False:
        listfield_callback[1] = lambda attr, obj, context: '<a href="%s">%s</a>' % (reverse(make_editable, kwargs=obj.__dict__), display_attribute(obj, attr))

    # id="pageTable" for ajax
    if not instance:
        instance = DataTableMako(classes=classes, wrapper=wrapper)
    instance.render(context, queryset, fields=fields, exclude=exclude, listfield_callback=listfield_callback, **kwargs)
    return instance.flush()

def grid(context, formset, fields=(), exclude=(), classes=(), instance=None, **kwargs):
    if not classes:
        classes = ['zebra', 'records', 'paging']
    if instance is None:
        instance = DataGridMako(classes=classes)
    instance.render(context, formset, fields=fields, exclude=exclude, **kwargs)
    return instance.flush()

class DataTableMako(DataTable):
    def render(self, context, queryset, fields=(), exclude=(), group=None, filter=None, row_filter=None, add_sort=False, stop_at=None, header=True, footer=False, listfield_callback=None, row_callback=lambda obj: u'<tr>', **kwargs):
        context.caller_stack._push_frame()
        self.context = context
        self.caller = context.get('caller', runtime.UNDEFINED)
        self.capture = context.get('capture', runtime.UNDEFINED)

        #Safing defaults
        fields = () if fields is runtime.UNDEFINED else fields
        exclude = () if exclude is runtime.UNDEFINED else exclude
        listfield_callback = {} if listfield_callback is None else listfield_callback

        #Custom Row handler
        if row_filter is not None and hasattr(self.caller, row_filter):
            row_callback = partial(self.capture, getattr(self.caller, row_filter))
            #self.writer(getattr(self.caller, row_filter(obj)))

        #CELL FILTERS ARE RETARDED.... IGNORE THEM FROM MAKO
        #Custom cell filter
        #if filter is not None and hasattr(self.caller, filter):
            #filter = partial(self.capture, getattr(self.caller, filter))# lambda obj, key: self.capture(, obj, key)
            #filter = getattr(self.caller, filter)

        #:TODO: this should be cache as to not re-run in the super class
        #Create listfield callback out of mako specfic variables
        columns = DataTableMako.expand_fields(queryset, fields, exclude)
        for key,label in columns:
            #FIRST COLUMN SPECIAL CASE ***DEPRECATED***
            if (key, label) == columns[0] and hasattr(self.caller, 'td__first'): #First column override :TODO: make this more generic
                #:TODO: I wish I didn't need to wrap this in a lambda, backward compat issue; also I don't know how passing context to a mako function works.
                listfield_callback[1] = partial(self.capture, lambda attr, obj, context: getattr(self.caller, 'td__first')(attr, obj))
            #:TODO: can we deprecate this too?
            if hasattr(self.caller, 'td_%s' % key):
                #:TODO: I wish I didn't need to wrap this in a lambda, backward compat issue; also I don't know how passing context to a mako function works.
                #listfield_callback[key] = lambda attr, obj, context: getattr(self.caller, 'td_%s' % attr)(obj)
                listfield_callback[key] = partial(self.capture, lambda attr, obj, context: getattr(self.caller, 'td_%s' % attr)(obj))

        try:
            super(DataTableMako, self).render(queryset, fields, exclude, group, filter, add_sort, stop_at, header, footer, listfield_callback, row_callback, **kwargs)
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
        if hasattr(self.caller, 'th_%s' % field):
            self.writer(self.capture(getattr(self.caller, 'th_%s' % field)))
        else:
            super(DataTableMako, self).render_header(field, label)

    def render_footer(self):
        #Can I do this in the main function to start with, or is context more important
        c = self.context.kwargs
        qs = c['request'].GET
        params = self.context.get('parameters', None)
        if params is None:
            return
        params['colspan'] = len(self.columns)
        params['qs_last'] = get_query_string(qs, {'page': -1})
        params['qs_first'] = get_query_string(qs, {'page': 1})
        params['qs_next'] = get_query_string(qs, {'page': params.get('next_page', '')})
        params['qs_prev'] = get_query_string(qs, {'page': params.get('prev_page', '')})
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


class DataGridMako(DataGrid):
    def render(self, context, formset, fields=(), exclude=(), **kwargs):
        context.caller_stack._push_frame()
        self.context = context
        self.caller = context.get('caller', runtime.UNDEFINED)
        self.capture = context.get('capture', runtime.UNDEFINED)

        try:
            super(DataGridMako, self).render(formset, fields, exclude, **kwargs)
        finally:
            context.caller_stack._pop_frame()






    
def render_vertical(context, data, fields=None):
    columns, output = [], []
    if not isinstance(data, dict):
        data = data.__dict__
    if fields is None:
        fields = data.keys()
    for f in fields:
        if isinstance(f, tuple):
            #(key, verbose)
            columns.append(f)
        else:
            columns.append((f,f))
    
    output.append(u'<table class="small zebra">')
    for f in fields:
        output.append(u'<tr><th>%s:</th><td>%s</td></tr>' % (f, data[f]))
    output.append(u'</table>')
    return SafeUnicode(''.join(output))
