from datetime import date, datetime
from mako import runtime
from django.forms.forms import pretty_name
from django.utils.safestring import SafeUnicode
from helpers.datatable.base import DataTable

from base import DataTable

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
    def render(self, context, queryset, fields=None, group=None, filter=None, row_filter=None, add_sort=False, stop_at=None, header=True, footer=False, listfield_callback=None, **kwargs):
        context.caller_stack._push_frame()
        
        self.context = context
        self.caller = context.get('caller', runtime.UNDEFINED)
        self.capture = context.get('capture', runtime.UNDEFINED)
        
        try:
            if fields is None or fields is runtime.UNDEFINED:
                fields = fields_for_model(queryset.model).keys()
            
            super(DataTableMako, self).render(queryset, fields, group, filter, row_filter, add_sort, stop_at, header, footer, listfield_callback, **kwargs)
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
        #:TODO: deprecate this
        if (key, label) == self.columns[0] and hasattr(self.caller, 'td__first'): #First column override :TODO: make this more generic
            return self.capture(getattr(self.caller, 'td__first'), key, obj)
    
        #:TODO: can we deprecate this too?
        if hasattr(self.caller, 'td_%s' % key):
            return self.capture(getattr(self.caller, 'td_%s' % key), obj)
        
        # TODO: WHAT WAS THIS FOR?
        #if 'next' in kwargs and hasattr(kwargs['next'], key):
        #    return self.capture(getattr(kwargs['next'], key), key, obj)
    
        #:TODO: is this even used? Deprecate... :: Filter this through specified function
        if self.filter is not None and hasattr(self.caller, self.filter):
            return self.capture(getattr(self.caller, self.filter), obj, key)
        
        return super(DataTableMako, self).get_column_value(obj, key, label, column_index)
    
