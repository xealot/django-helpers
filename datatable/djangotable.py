from base import BaseTable
from plugins import *
from ..general import get_default_fields
from django.db.models import Count


class ModelTable(BaseTable):
    def prepare_columns(self, queryset, columns, exclude):
        if columns:
            # When columns are specified, only use them as specified.
            if isinstance(columns[0], basestring):
                new_columns = [(c, c) for c in columns]
            else:
                new_columns = [c for c in columns]
            return new_columns
        else:
            # Columns not known, pull them from the model.
            if hasattr(queryset, 'model'):
                return get_default_fields(queryset.model, (), exclude or None, include_verbose=True)
    
    def get_data(self, row_data, column_name):
        return getattr(row_data, column_name)
