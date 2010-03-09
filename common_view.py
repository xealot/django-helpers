"""
This is a python wildcard import for common view necessities. Just use:

from helpers.common_view import *
"""
from django.utils.text import capfirst
from django.utils.datastructures import SortedDict
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.contrib.admin.templatetags.admin_list import results
from urllib import urlencode
from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, get_list_or_404, _get_queryset
from django.template import RequestContext, loader, Context
from django.views.decorators.vary import vary_on_headers, vary_on_cookie
from django.views.decorators.cache import never_cache
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.forms.models import modelform_factory, modelformset_factory
from django.contrib import messages

from django.db import transaction
from django.db.transaction import commit_on_success
from django.db.models import Q
from django.db.models.aggregates import Count
from helpers.tablejax import ajax_table_page
from helpers.utilities import direct_to_template, post_data, render_to_response, redirect, redirect_to_referrer, render_to




from django.contrib.auth.decorators import login_required
from helpers.utilities import render_to_response as r2r