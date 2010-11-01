"""
Data table plugins
"""
from cgi import escape
from base import DTPluginBase
from lxml import etree
from lxml.html import builder as E
from django.utils.encoding import force_unicode

#General Formatt needs these deps
import datetime
from decimal import Decimal
from django.utils.safestring import SafeUnicode, SafeString
from django.utils.text import capfirst
from django.utils import dateformat
from django.conf import settings


def xmlstring(xmltable, method='xml', encoding=unicode, pretty_print=False):
    if isinstance(xmltable, (list, tuple)):
        return ''.join([etree.tostring(i, method=method, encoding=encoding, pretty_print=pretty_print) for i in xmltable])
    return etree.tostring(xmltable, method=method, encoding=encoding, pretty_print=pretty_print)


class DTUnicode(DTPluginBase):
    def header(self, callchain, column_index):
        return force_unicode(callchain.chain)

    def cell(self, callchain, data, column_index, column_name, row_number):
        if isinstance(callchain.chain, basestring):
            return force_unicode(escape(callchain.chain))


class DTGeneralFormatter(DTPluginBase):
    def _format(self, value, label, cast=None, null='(None)', empty='(Empty)', places=2, map=None, max_length=100, truncate='...'):
        """Intelligently format typed data"""
        if value is None:
            value = null % {'label': label}
        if cast is not None:
            value = cast(value)
    
        if isinstance(value, (datetime.datetime, datetime.time, datetime.date)):
            if isinstance(value, datetime.datetime):
                result_repr = capfirst(dateformat.format(value, settings.DATE_FORMAT))
            elif isinstance(value, datetime.time):
                result_repr = capfirst(dateformat.time_format(value, settings.TIME_FORMAT))
            else:
                result_repr = capfirst(dateformat.format(value, settings.DATE_FORMAT))
        elif isinstance(value, bool):
            BOOLEAN_MAPPING = {True: 'yes', False: 'no', None: 'unknown'}
            result_repr = E.IMG(src="%simg/admin/icon-%s.gif" % (settings.ADMIN_MEDIA_PREFIX, BOOLEAN_MAPPING[value]), alt="%s" % value)
        elif isinstance(value, (float, Decimal)):
            result_repr = (u'%%.%sf' % places) % value
        elif map:
            result_repr = map.get(value, '--')
        elif isinstance(value, (SafeUnicode, SafeString)):
            try:
                return etree.fromstring(value)
            except etree.XMLSyntaxError:
                result_repr = value
        else:
            result_repr = unicode(value)
        
        if empty and result_repr == '':
            result_repr = empty % {'label': label} 
        
        if not isinstance(result_repr, (SafeUnicode, SafeString)) and max_length and len(result_repr) > max_length:
            result_repr = E.ABBR(result_repr[:max_length-len(truncate)] + truncate, title=result_repr)
        return result_repr
    
    def cell(self, callchain, data, column_index, column_name, row_number):
        return self._format(callchain.chain, column_name)


class DTHtmlTable(DTPluginBase):
    REQUIRES = [DTUnicode]
    def head(self, callchain):
        return E.THEAD(*callchain.chain)
    
    def header(self, callchain, column_index):
        return E.TH(callchain.chain)

    def body(self, callchain):
        return E.TBODY(*callchain.chain)
    
    def row(self, callchain, data, row_number):
        return E.TR(*callchain.chain)
    
    def cell(self, callchain, data, column_index, column_name, row_number):
        return E.TD(callchain.chain)

    def finalize(self, callchain):
        return E.TABLE(*callchain.chain)


class DTWrapper(DTPluginBase):
    REQUIRES = [DTHtmlTable]
    def __init__(self, classes, **kwargs):
        self.classes, self.attrs = classes, kwargs

    def finalize(self, callchain):
        elem = E.TABLE(*callchain.chain, **self.attrs)
        if self.classes:
            self.add_class(elem, self.classes)
        return elem


class DTZebra(DTPluginBase):
    REQUIRES = [DTHtmlTable]
    def __init__(self, odd='odd', even='even'):
        self.odd, self.even = odd, even
        
    def row(self, callchain, data, row_number):
        return self.add_class(callchain.chain, row_number % 2 == 0 and [self.odd] or [self.even])


class DTJsSort(DTPluginBase):
    REQUIRES = [DTHtmlTable]
    """This class adds javascript sorting to the table headers and tag."""
    def finalize(self, callchain):
        return self.add_class(callchain.chain, ['sortable'])


class DTRowLimit(DTPluginBase):
    """This class stops the table at a certain amount of rows"""
    def __init__(self, limit):
        self.limit = limit
    
    def row(self, callchain, data, row_number):
        if row_number > self.limit:
            raise StopIteration()


class DTGroupBy(DTPluginBase):  
    REQUIRES = [DTHtmlTable] 
    """This class stops the table at a certain amount of rows"""
    def __init__(self, column):
        self.column = column
        self.last_value = None
    
    def row(self, callchain, data, row_number):
        value = callchain.instance.get_data(data, self.column)
        if self.last_value != value:
            self.last_value = value
            colspan = str(len(callchain.chain))
            groupby = E.TR(E.TD(value, E.CLASS(self.add_class_string(callchain.chain.get('class'), ['group'])), colspan=colspan))
            callchain.pre(groupby)


class DTCallback(DTPluginBase):
    """
    This class executes a callback for fields that require it.
    
    There is some super hacky shit making this work right now, as you can see in CELL. I should 
    probably work to remove this garbage.
    """
    def __init__(self, callbacks, header_callbacks=None):
        self.callbacks = callbacks
        self.header_callbacks = header_callbacks

    def header(self, callchain, column_index):
        callback = None
        if column_index in self.header_callbacks:
            callback = self.header_callbacks[column_index]
        if callback is not None:
            value = '<span>%s</span>' % callback(column_index, data)
            if isinstance(value, basestring):
                #HACK HACK HACK HACK, lxml is supergay when it comes to HTML or not-html. Just can't insert TEXT and have it play nice.
                #God forbid bad HTML should come along.
                try:
                    return etree.fromstring(value)
                except etree.XMLSyntaxError:
                    return value
            elif isinstance(value, (list, tuple)):
                return [etree.fromstring(i) for i in value]
            return value
    
    def cell(self, callchain, data, column_index, column_name, row_number):
        callback = None
        if column_index in self.callbacks:
            callback = self.callbacks[column_index]
        if column_name in self.callbacks:
            callback = self.callbacks[column_name]
        if callback is not None:
            value = '<span>%s</span>' % callback(column_name, data)
            if isinstance(value, basestring):
                #HACK HACK HACK HACK, lxml is supergay when it comes to HTML or not-html. Just can't insert TEXT and have it play nice.
                #God forbid bad HTML should come along.
                try:
                    return etree.fromstring(value)
                except etree.XMLSyntaxError:
                    return value
            elif isinstance(value, (list, tuple)):
                return [etree.fromstring(i) for i in value]
            return value

class DTSelectable(DTPluginBase):
    REQUIRES = [DTHtmlTable]
    def __init__(self, attribute, checkbox_name='selection', index=0):
        self.attribute, self.checkbox_name, self.index = attribute, checkbox_name, index

    def finalize(self, callchain):
        self.add_class(callchain.chain, ['selectable'])

    def head(self, callchain):
        callchain.chain.insert(self.index, E.TH(
            E.INPUT(E.CLASS('master'), type='checkbox', name='%s-master' % self.checkbox_name), 
        width='1'))

    def row(self, callchain, data, row_number):
        callchain.chain.insert(self.index, E.TD(E.INPUT(type='checkbox', name=str(self.checkbox_name), value=str(callchain.instance.get_data(data, self.attribute)))))
    

class DTRowFormatter(DTPluginBase):
    REQUIRES = [DTHtmlTable]
    def __init__(self, test=lambda data, row_number: False, style=None, css=None):
        self.test, self.style, self.css = test, style, css

    def row(self, callchain, data, row_number):
        if self.test(data):
            self.add_class(callchain.chain, self.css)


class DTSpecialFooter(DTPluginBase):
    REQUIRES = [DTHtmlTable]
    """This class adds a super footer to the table"""
    def footer(self, callchain):
        return E.TFOOT()



#########
# NG SPECIFIC
#########

class DTLinker(DTPluginBase):
    def __init__(self, index, resolver=lambda name, data: '#', **kwargs):
        self.index, self.resolver, self.attrs = index, resolver, kwargs

    def cell(self, callchain, data, column_index, column_name, row_number):
        if column_index == self.index or column_name == self.index:
            callchain.chain.append(E.A(callchain.chain.text, href=self.resolver(column_name, data), **self.attrs))
            callchain.chain.text = None


from ..querystring import morph
class DTPagingFooter(DTPluginBase):
    def __init__(self, params):
        self.params = params

    def head(self, callchain):
        self.colspan = str(len(callchain.chain))

    def footer(self, callchain):
        return E.TFOOT(id='ajaxPager', *callchain.chain)

    def foot(self, callchain):
        querystring = dict([(i,v) for i,v in self.params._asdict().items() if i in ('page', 'limit', 'sort', 'dir')])
        params = {}
        params['colspan'] =     self.colspan
        params['records'] =     self.params.records
        params['page'] =        self.params.page
        params['pages'] =       self.params.pages
        params['start'] =       self.params.start
        params['end'] =         self.params.end
        params['qs_last'] =     morph(querystring, page=self.params.pages)
        params['qs_first'] =    morph(querystring, page=1)
        params['qs_next'] =     morph(querystring, page=self.params.next_page)
        params['qs_prev'] =     morph(querystring, page=self.params.prev_page)
        params['qs_limit_25'] = morph(querystring, limit=25)
        params['qs_limit_50'] = morph(querystring, limit=50)
        params['qs_limit_100'] =morph(querystring, limit=100)
        
        return etree.fromstring(u"""
        <tr class="frow pager">
            <td colspan="%(colspan)s">
                <div style="width: 33%%; float:left;">
                    Records: <span id="ajaxRecordFrom">%(start)s</span> to <span id="ajaxRecordTo">%(end)s</span> of <span id="ajaxRecords">%(records)s</span>
                </div>
                <div style="width: 33%%; float:left; text-align: center;">
                    <a href="%(qs_first)s" rel="history" class="table_first">First</a>
                    <a href="%(qs_prev)s" rel="history" class="table_prev">Prev</a>
                    Page %(page)s
                    <!-- <input type="text" style="width: 20px;" id="ajaxPageNo" value="%(page)s"/> --> 
                    of <span id="ajaxPages">%(pages)s</span>  
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
        </tr>""" % params)

