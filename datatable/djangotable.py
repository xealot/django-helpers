from base import BaseTable
from plugins import *
from ..general import get_default_fields
from django.db.models import Count


class ModelTable(BaseTable):
    def build_headers(self, data, columns):
        headers = []
        for header in columns:
            headers.extend(self.header(header))
        return headers or None
    
    def prepare_columns(self, queryset, columns, exclude):
        if columns:
            # When columns are specified, only use them as specified.
            if len(columns[0]) == 1:
                new_columns = [(c, c) for c in columns]
            else:
                new_columns = [c for c in columns]
            return new_columns
        else:
            # Columns not known, pull them from the model.
            if hasattr(queryset, 'model'):
                return get_default_fields(queryset.model, (), exclude or None, include_verbose=True)
    
    def build_body(self, data, columns):
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
qs = AmexIndex.objects.annotate(num_entries=Count('id')).all()[:5]

bt = ModelTable(include_header=True, plugins=(DTUnicode, DTHtmlTable, DTWrapper(style='width: 100%;'), DTZebra, DTJsSort, DTSpecialFooter))
print etree.tostring(bt.output(qs), method='html', encoding=unicode, pretty_print=True)
