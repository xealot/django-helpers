from base import BaseTable
from plugins import *
from ..general import get_default_fields
from django.db.models import Count


class ModelTable(BaseTable):
    def prepare_columns(self, queryset, columns, exclude):
        if columns:
            # When columns are specified, only use them as specified.
            new_columns = []
            for column in columns:
                if isinstance(column, basestring):
                    # Get labels for what we can.
                    if queryset.model:
                        f = queryset.model._meta.get_field(column)
                        if f:
                            new_columns.append([column, f.verbose_name.title()])
                            continue
                    new_columns.append([column, column])
                else:
                    new_columns.append(column)
            return new_columns
        else:
            # Columns not known, pull them from the model.
            if hasattr(queryset, 'model'):
                return get_default_fields(queryset.model, (), exclude or None, include_verbose=True)
    
    def get_data(self, row_data, column_name):
        return getattr(row_data, column_name, None)
