"""
Data table plugins
"""
from lxml import etree
from lxml.html import builder as E
from django.utils.encoding import force_unicode


def xmlstring(xmltable, method='xml', encoding=unicode, pretty_print=False):
    return etree.tostring(xmltable, method=method, encoding=encoding, pretty_print=pretty_print)


class DTPluginBase(object):
    REQUIRES = []
    def _get_classes_string(self, classes):
        return classes and set(classes.split(' ')) or set()
    
    def _get_classes(self, element):
        return self._get_classes_string(element.get('class', ''))
    
    def add_class_string(self, classes, new_classes=()):
        newset = self._get_classes_string(classes)
        newset.update(set(new_classes))
        return ' '.join(newset)
    
    def add_class(self, element, classes=(), iterate=True):
        if iterate and isinstance(element, (list,tuple)):
            for e in element:
                self.add_class(e, classes, iterate=False)
            return element
        else:
            css = self._get_classes(element)
            css.update(classes)
            element.set('class', ' '.join(css))
            return element
        
    def remove_class(self, element, classes=()):
        css = self._get_classes(element)
        css.difference(classes)
        element.set('class', ' '.join(css))
        return element


class DTUnicode(DTPluginBase):
    def header(self, callchain, column_index):
        return force_unicode(callchain.chain)

    def cell(self, callchain, data, row_number, column_index):
        return force_unicode(callchain.chain)


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
    
    def cell(self, callchain, data, row_number, column_index):
        return E.TD(callchain.chain)

    def finalize(self, callchain):
        return E.TABLE(*callchain.chain)


class DTWrapper(DTPluginBase):
    REQUIRES = [DTHtmlTable]
    def __init__(self, **kwargs):
        self.attrs = kwargs

    def finalize(self, callchain):
        return E.TABLE(*callchain.chain, **self.attrs)


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


class DTSpecialFooter(DTPluginBase):
    REQUIRES = [DTHtmlTable]
    """This class adds a super footer to the table"""
    def footer(self, callchain):
        return E.TFOOT()


class DTGroupBy(DTPluginBase):  
    REQUIRES = [DTHtmlTable] 
    """This class stops the table at a certain amount of rows"""
    def __init__(self):
        pass
    
    def row(self, callchain, data, row_number):
        colspan = str(len(callchain.chain))
        groupby = E.TR(E.TD('GROUP', E.CLASS(self.add_class_string(callchain.chain.get('class'), ['group'])), colspan=colspan))
        callchain.pre(groupby)


class DTCallback(DTPluginBase):
    """This class executes a callback for fields that require it."""
    def __init__(self, callbacks):
        self.callbacks = callbacks
    
    def cell(self, callchain, data, row_number, column_index):
        if column_index in self.callbacks:
            callback = self.callbacks[column_index]
            return callback(column_index, data)


class DTSelectable(DTPluginBase):
    REQUIRES = [DTHtmlTable]
    def __init__(self, attribute, checkbox_name='selection', index=0):
        self.attribute, self.checkbox_name, self.index = attribute, checkbox_name, index

    def finalize(self, callchain):
        self.add_class(callchain.chain, ['selectable'])

    def head(self, callchain):
        callchain.chain.insert(self.index, E.TH(width='1'))

    def row(self, callchain, data, row_number):
        callchain.chain.insert(self.index, E.TD(E.INPUT(type='checkbox', name=self.checkbox_name, value=callchain.instance.get_data(data, self.attribute))))
    

class DTRowFormatter(DTPluginBase):
    REQUIRES = [DTHtmlTable]
    def __init__(self, test=lambda row_number: False, style=None, css=None):
        self.test, self.style, self.css = test, style, css

    def row(self, callchain, data, row_number):
        if self.test(row_number):
            self.add_class(callchain.chain, [])






