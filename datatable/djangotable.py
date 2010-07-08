from base import BaseTable
from plugins import *

class ModelTable(BaseTable):
    def build_headers(self, data):
        headers = []
        for header in self.get_headers(data):
            headers.extend(self.header(header))
        return headers or None
    
    def get_headers(self, initial):
        if initial:
            return initial[0].keys()
        return ()
    
    def build_body(self, data):
        body_data, row_number = [], 0
        for model in data:
            row_number += 1
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
