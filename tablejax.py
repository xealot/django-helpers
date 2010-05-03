#Excessive Space Removal RE
import re
from django.http import HttpResponse
from django.db.models import Q
from django.template import loader
from django.template.context import RequestContext

tab_return_re = re.compile('[\t\n\r]+| {2,}', re.MULTILINE)

def render_buildtable(request, queryset, template, fields, default_sort=None, search_fields=None, **kwargs):
    #from helpers.mako_integration import get_request_context, mylookup
    context = RequestContext(request, {'pager': True, 'sorting': True, 'group_by': None, 'selectable': False})
    context.update(kwargs)
    if context['selectable']:
        fields.append('cap')
    context_dict = {}
    for d in context.dicts:
        context_dict.update(d)
    template = loader.get_template(template)
    table_body = template.template.get_def("buildtable").render_unicode(queryset, fields=fields, **context_dict)
    table_body = tab_return_re.sub(' ', table_body)
    return table_body

def ajax_table_page(request, queryset, default_sort=None, search_fields=None, **kwargs):
    from math import ceil
    from django.utils import simplejson as json
    from django.db.models.sql.query import get_order_dir
    #from helpers.mako_integration import get_request_context, mylookup

    pageVars = request.GET.copy()
    qs = queryset    
    ajax = {'rows': [], 'records': 0, 'limit': 25, 'pages': 1, 'page': 1, 'range': [0,0], 'sort': 'pk', 'dir': 'ASC', 'filter': ''}

    #Insure Integers
    intVars = ['limit']
    for v in intVars:
        try:
            pageVars[v] = int(pageVars.get(v, ajax.get(v, 0)))
        except ValueError:
            pageVars[v] = ajax.get(v, 0)

    filter = pageVars.get('filter', '')
    sort = pageVars.get('sort', 'pk')
    if sort == 'pk' and hasattr(qs, 'query') and qs.query.order_by:
        pageVars['sort'], pageVars['dir'] = get_order_dir(qs.query.order_by[0])

    dir = pageVars.get('dir', 'ASC')
    page = pageVars.get('page', 1)
    
    try:
        if page != 'LAST':
            page = int(page)
    except ValueError:
        page = ajax.get('page', 1) 

    if filter and search_fields:
        search = Q()
        for field in search_fields:
            search = search | Q(**{'%s__icontains' % field: filter})
        qs = qs.filter(search)

    size = qs.count()
    qs = qs.order_by('%s%s' % ('-' if dir == 'DESC' else '', sort))

    limit = pageVars.get('limit')

    if size > 0 and limit > 0:
        pages = int(ceil(float(size)/float(limit)))
    else:
        pages = 1
    if page == 'LAST' or page > pages:
        page = pages
    elif page < 1:
        page = 1

    start = int(pageVars.get('start', 0)) or (page*limit)-limit
    end = start+limit
    if start+limit > size:
        page = pages
        start = (page*limit)-limit
        end = size
        
    qs = qs[start:end]

    ajax.update({'limit': limit,
                 'records': size, 
                 'pages': pages, 
                 'page': page, 
                 'range': [start,end], 
                 'sort': sort, 
                 'dir': dir,
                 'filter': filter})

    table_body = render_buildtable(request, qs, **kwargs)
    returnData = {'meta': ajax, 'html': table_body}
    response = json.dumps(returnData, ensure_ascii=False)
    return HttpResponse(response, 'text/plain')