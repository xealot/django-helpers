from base import BaseTable
from plugins import *
from ..general import get_default_fields
from django.db.models import Count
from django.db.models.fields import FieldDoesNotExist


class ModelTable(BaseTable):
    def prepare_columns(self, queryset, columns, exclude):
        if columns:
            # When columns are specified, only use them as specified.
            new_columns = []
            for column in columns:
                if isinstance(column, basestring):
                    # Get labels for what we can.
                    if queryset.model:
                        try:
                            f = queryset.model._meta.get_field(column)
                            new_columns.append([column, f.verbose_name.title()])
                        except FieldDoesNotExist:
                            new_columns.append([column, column])
                else:
                    new_columns.append(column)
            return new_columns
        else:
            # Columns not known, pull them from the model.
            if hasattr(queryset, 'model'):
                return get_default_fields(queryset.model, (), exclude or None, include_verbose=True)
    
    def get_data(self, row_data, column_name):
        opts = row_data._meta
        try:
            f = opts.get_field(column_name)
        except models.FieldDoesNotExist:
            # For non-field values, the value is either a method, property or
            # returned via a callable.
            if callable(column_name):
                attr = column_name
                value = attr(row_data)
            else:
                attr = getattr(row_data, column_name)
                if callable(attr):
                    value = attr()
                else:
                    value = attr
            f = None
        else:
            attr = None
            value = getattr(row_data, column_name)
        return f, attr, value
