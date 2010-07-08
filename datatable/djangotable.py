from base import BaseTable
from plugins import *

class ModelTable(BaseTable):
    def build(self, data):
        """Accepts any iterable with subscriptable access"""
        element_list = []
        
        #Process Headers
        if self.include_header:
            hdrs = self.build_headers(data)
            if hdrs is not None:
                element_list.extend(self.head(hdrs))
        
        element_list.extend(self.body(self.build_body(data))) #Process Body
        
        #Optional Footer
        if self.include_footer:
            ftrs = self.build_footer(data)
            if ftrs is not None:
                element_list.extend(self.footer(ftrs))

        return self.finalize(element_list)[0]

    def output(self, data):
        """Build and output data"""
        #return etree.tostring(self.build(data), method='html', encoding=unicode, pretty_print=True)
        return self.build(data)
    
    def build_headers(self, data):
        headers = []
        for header in self.get_headers(data):
            headers.extend(self.header(header))
        return headers or None
    
    def build_footer(self, data):
        footer = self.footer(data)
        if data is footer[0]:
            return None
        return footer
    
    def get_headers(self, initial):
        if initial:
            return initial[0].keys()
        return ()
    
    def build_body(self, data):
        body_data, row_number = [], 0
        for model in data:
            row_number+=1
            cells = []
            for field in model._meta.fields:
                cells.extend(self.cell(getattr(model, field.name), data=model, row_number=row_number, column_index=field.name))
            try: 
                body_data.extend(self.row(cells, row_number=row_number))
            except StopIteration:
                break
        return body_data
        

from stocks.models import AmexIndex
qs = AmexIndex.objects.all()[:5]

bt = ModelTable(include_header=False, plugins=(DTUnicode, DTHtmlTable, DTWrapper(style='width: 100%;'), DTZebra, DTJsSort, DTSpecialFooter))
print etree.tostring(bt.output(qs), method='html', encoding=unicode, pretty_print=True)
