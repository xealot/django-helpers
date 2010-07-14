from base import BaseTable
from plugins import *
from ..general import get_default_fields
from django.db.models import Count
from django.db.models.fields import FieldDoesNotExist
from django.forms.forms import pretty_name
from django.utils.safestring import mark_safe


class ModelTable(BaseTable):
    def prepare_columns(self, queryset, columns, exclude):
        if columns:
            # When columns are specified, only use them as specified.
            new_columns = []
            for column in columns:
                if isinstance(column, (list, tuple)):
                    new_columns.append(column)
                else:
                    # Get labels for what we can.
                    if queryset.model:
                        try:
                            f = queryset.model._meta.get_field(column)
                            new_columns.append([column, pretty_name(f.verbose_name)])
                        except FieldDoesNotExist:
                            if callable(column):
                                column_verbose = getattr(column, 'short_description', pretty_name(column.func_name))
                            else:
                                attr = getattr(queryset.model, column, None)
                                if attr is not None and callable(attr):
                                        column_verbose = getattr(attr, 'short_description', pretty_name(attr.func_name))
                                else:
                                    column_verbose = pretty_name(column)
                            new_columns.append([column, column_verbose])
                    else:
                        new_columns.append([column, pretty_name(column)])
            return new_columns
        else:
            # Columns not known, pull them from the model.
            if hasattr(queryset, 'model'):
                return get_default_fields(queryset.model, (), exclude or None, include_verbose=True)
    
    def get_data(self, row_data, column_name):
        try:
            f = row_data._meta.get_field(column_name)
        except FieldDoesNotExist:
            # For non-field values, the value is either a method or
            # returned via a callable.
            if callable(column_name):
                attr = column_name
                value = attr(row_data)
            else:
                attr = getattr(row_data, column_name, None)
                if attr is not None and callable(attr):
                    value = attr()
                else:
                    value = attr
            f = None
        else:
            attr = None
            value = getattr(row_data, column_name)
        return value


class FormsetTable(BaseTable):
    def iterate(self, data):
        for i in data.forms:
            yield i
            
    def prepare_columns(self, formset, columns, exclude):
        if columns:
            # When columns are specified, only use them as specified.
            new_columns = []
            for column in columns:
                if isinstance(column, basestring):
                    new_columns.append([column, column])
                else:
                    new_columns.append(column)
            return new_columns
        elif formset:
            first_form = formset.forms[0]
            return [(f.name, f.label) for f in first_form.visible_fields()]

    def get_data(self, row_data, column_name):
        return mark_safe(row_data[column_name])
