from base import DTPluginBase
from plugins import xmlstring, DTGeneralFormatter, DTUnicode, DTHtmlTable, DTWrapper, DTSelectable, DTCallback, DTPagingFooter, DTLinker
from djangotable import ModelTable
from makotable import NGLegacyCSS



def get_plugins(queryset, params, record_url=None, fields=(), exclude=(), listfield_callback=None, make_selectable=False, linker=False, wrapper=False, additional_plugins=()):
    classes = ['zebra', 'records', 'paging']
    if record_url is not None:
        classes.append("{record_url: '%s'}" % record_url)
        
    plugins = [DTGeneralFormatter, DTUnicode, DTHtmlTable, NGLegacyCSS]
    if wrapper is not False:
        plugins.append(DTWrapper(classes=classes, style='width: 100%;'))
    #if listfield_callback:
    #    plugins.insert(2, DTCallback(listfield_callback))
    if make_selectable is not False:
        plugins.append(DTSelectable(make_selectable))
    if linker is not False:
        plugins.append(DTLinker(**linker))
    plugins.append(DTPagingFooter(params)) #This comes last since it needs to calc colspan.
    plugins.extend(additional_plugins)
    return plugins

def stub(queryset, params, record_url, fields=(), exclude=(), listfield_callback=None, make_selectable=False, linker=False, additional_plugins=()):
    plugins = get_plugins(queryset, params, record_url, fields, exclude, listfield_callback, make_selectable, linker, wrapper=True, additional_plugins=additional_plugins)
    table = ModelTable(plugins=plugins)
    return xmlstring(table.build(queryset, columns=fields, exclude=exclude))

def table(queryset, params, fields=(), exclude=(), listfield_callback=None, make_selectable=False, linker=False, additional_plugins=()):
    record_url = None
    plugins = get_plugins(queryset, params, record_url, fields, exclude, listfield_callback, make_selectable, linker, additional_plugins)
    table = ModelTable(plugins=plugins, include_header=False, include_footer=False, finalize=False)
    return xmlstring(table.build(queryset, columns=fields, exclude=exclude))