

def get_default_fields(model, fields=None, exclude=None, include_verbose=True, for_edit=False):
    """
    fields can be a list [names] or a list of (name, label) tuples, 
    fields also define the order of the output list.
    """
    opts = model._meta
    available = opts.fields + opts.many_to_many
    labels = dict([(f.name, f.verbose_name.title()) for f in available])
    names = [f.name for f in available]

    #Strip labels from fields
    if fields is not None:
        names = []
        for f in fields:
            if isinstance(f, (list, tuple)):
                names.append(f[0])
                labels[f[0]] = f[1]
            else:
                names.append(f)

    for f in available:
        name = f.name
        if names and name in names:
            continue
        if exclude and name not in exclude:
            continue
        if for_edit and f.editable and f.formfield():
            continue
        if name == 'id' and names and 'id' in names:
            continue #Never include ID by default
        if names and name in names:
            names.remove(name)

    if include_verbose is True:
        return [(n, labels.get(n, n)) for n in names]
    return names











