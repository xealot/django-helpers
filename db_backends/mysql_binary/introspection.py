from MySQLdb.constants import FIELD_TYPE
from django.db.backends.mysql.introspection import DatabaseIntrospection as MySQLBaseDatabaseIntrospection

class DatabaseIntrospection(MySQLBaseDatabaseIntrospection):
    data_types_reverse = {
        FIELD_TYPE.BLOB: 'TextField',
        FIELD_TYPE.CHAR: 'CharField',
        FIELD_TYPE.DECIMAL: 'DecimalField',
        FIELD_TYPE.NEWDECIMAL: 'DecimalField',
        FIELD_TYPE.DATE: 'DateField',
        FIELD_TYPE.DATETIME: 'DateTimeField',
        FIELD_TYPE.DOUBLE: 'FloatField',
        FIELD_TYPE.FLOAT: 'FloatField',
        FIELD_TYPE.INT24: 'IntegerField',
        FIELD_TYPE.LONG: 'IntegerField',
        FIELD_TYPE.LONGLONG: 'BigIntegerField',
        FIELD_TYPE.SHORT: 'IntegerField',
        FIELD_TYPE.STRING: 'CharField',
        FIELD_TYPE.TIMESTAMP: 'DateTimeField',
        FIELD_TYPE.TINY: 'IntegerField',
        FIELD_TYPE.BLOB: 'BlobField',
        FIELD_TYPE.LONG_BLOB: 'BlobField',
        FIELD_TYPE.TINY_BLOB: 'BlobField',
        FIELD_TYPE.MEDIUM_BLOB: 'BlobField',
        FIELD_TYPE.VAR_STRING: 'CharField',
    }

