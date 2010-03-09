from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper
from django.db.backends.mysql.base import DatabaseOperations as MySQLDatabaseOperations
from django.db.backends.mysql.base import *
from django.utils.encoding import smart_unicode

from client import DatabaseClient
from creation import DatabaseCreation
from introspection import DatabaseIntrospection
from validation import DatabaseValidation

binstr_conversion = [(FLAG.BINARY, buffer),
                     (FLAG.BLOB, smart_unicode),
                     ]

django_conversions.update({
    FIELD_TYPE.TINY_BLOB: binstr_conversion,
    FIELD_TYPE.MEDIUM_BLOB: binstr_conversion,
    FIELD_TYPE.LONG_BLOB: binstr_conversion,
    FIELD_TYPE.BLOB: binstr_conversion,
    FIELD_TYPE.VARCHAR: binstr_conversion,
    FIELD_TYPE.VAR_STRING: binstr_conversion,
    FIELD_TYPE.STRING: binstr_conversion,
})


class DatabaseOperations(MySQLDatabaseOperations):
    def last_executed_query(self, cursor, sql, params):
        """
        Returns a string of the query last executed by the given cursor, with
        placeholders replaced with actual values.

        `sql` is the raw query containing placeholders, and `params` is the
        sequence of parameters. These are used by default, but this method
        exists for database backends to provide a better implementation
        according to their own quoting schemes.
        """
        from django.utils.encoding import smart_unicode, force_unicode

        # Convert params to contain Unicode values.
        #to_unicode = lambda s: force_unicode(s, strings_only=True)
        def to_unicode(s):
            if isinstance(s,buffer):
                return u'<binary data buffer size %d>' % len(s)
            return force_unicode(s, strings_only=True)
        
        if isinstance(params, (list, tuple)):
            u_params = tuple([to_unicode(val) for val in params])
        else:
            u_params = dict([(to_unicode(k), to_unicode(v)) for k, v in params.items()])

        return smart_unicode(sql) % u_params


class DatabaseWrapper(MySQLDatabaseWrapper):
    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
    
        self.server_version = None
        self.features = DatabaseFeatures()
        self.ops = DatabaseOperations()
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        self.validation = DatabaseValidation(self)

