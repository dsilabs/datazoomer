
from helpers import link_to, url_for, name_for
from system import system
from request import route
from tools import unisafe, as_actions

def browse2(items,
            labels=None, columns=None, fields=None,
            footer=None, actions=None, caption=None,
            classed="table table-striped table-hover", nowrap=False, sortable=True,
            on_click=None, on_delete=None, on_remove=None,
            *args, **keywords):
    """
        footer: footer string or list of column footers
        actions: dz actions
        caption: table caption string (use css to locate/format)
        classed: css class string or a list of css classes for the table
        nowrap: the width to check as to whether to add a cell nowrap class (default is False -> off or do not use)
        sortable: truthy/falsey as to whether to use the jquery tablesorter (on by default)
    """

    def trash_can(key,kind,action,**args):
        link  = url_for(str(key),action,**args)
        tpl = '<td><a href="{link}" class="{kind}"><img src="/static/dz/images/{kind}.png" alt="{kind}"></a></td>'
        return tpl.format(**locals())

    def getcol(item, index):
        try:
            if type(item) in  [dict, tuple, list]:
                return item[index]
            else:
                return getattr(item, index)
        except (AttributeError, KeyError, TypeError), e:
            return ''
        except:
            raise

    if labels:
        if not columns:
            if len(items) and hasattr(items[0], 'get'):
                columns = [name_for(label).lower() for label in labels]

            elif len(items) and hasattr(items[0], '__len__') and len(items[0]):
                columns = range(len(labels))

            else:
                columns = [name_for(label).lower() for label in labels]

    else:
        if columns:
            labels = columns
        else:
            if len(items) and hasattr(items[0], 'keys') and callable(getattr(items[0],'keys')):
                labels = columns = items[0].keys()

            elif len(items) and hasattr(items[0], '__dict__'):
                labels = columns = [items[0].__dict__.keys()]

            elif len(items) and hasattr(items[0], 'keys') and callable(getattr(items[0],'keys')):
                labels = columns = [items[0].keys()]

            elif len(items) and hasattr(items[0], '__len__') and len(items[0]):
                labels = items[0]
                columns = range(len(items[0]))
                items = items[1:]

            else:
                if len(items):
                    raise Exception('{}'.format(hasattr(items[0],'__len__')))
                raise Exception('Unable to infer columns')

    columns = list(columns)
    labels = list(labels)

    if fields:
        lookup = fields.as_dict()
        for col in columns[len(labels):]:
            if col in lookup:
                label = lookup[col].label
            else:
                label = col
            labels.append(label)

        alist = []
        for item in items:
            fields.initialize(item)
            flookup = fields.display_value()
            row = [flookup.get(col.upper(),getcol(item,col)) for col in columns]
            alist.append(row)
    else:
        alist = [[getcol(item,col) for col in columns] for item in items]

    if (on_click or on_delete or on_remove) and columns[0] <> '_id':
        columns = ['_id'] + columns
        t = []
        for i in alist:
            t.append([i[0]] + i)
        alist = t

    head = labels[:]
    if head and on_delete: head.append(' ')
    if head and on_remove: head.append(' ')

    body = []
    for count, row in enumerate(alist, start=1):
        body.append( '<tr class="row-{}">'.format(count) )

        for colnum, item in enumerate(row):
            wrapping = (nowrap and len(unisafe(item)) < nowrap) and '<td class="nowrap">{}</td>' or '<td>{}</td>'
            if (on_click or on_delete or on_remove) and colnum == 0:
                key = item
            if on_click and (colnum == 1 or colnum==0 and len(row)==1):
                url = '/'.join(route[1:]+[str(key)])
                body.append(wrapping.format(link_to(item, url, *args, **keywords)))
            elif colnum>0 or not (on_click or on_remove or on_delete):
                body.append(wrapping.format(unisafe(item)))

        if on_delete:
            body.append(trash_can(key,'delete',on_delete))

        if on_remove:
            body.append(trash_can(key,'remove',on_remove))

        body.append( '</tr>' )

    selector = hasattr(classed, '__iter__') and '.'.join(classed) or classed
    selector = "{}".format(selector.replace(' ', '.'))
    classed = hasattr(classed, '__iter__') and ' '.join(classed) or classed
    actions = actions and '<div class="actions">{}</div>'.format(as_actions(actions)) or ''
    caption = caption and "<caption>{}</caption>".format(caption) or ''
    head = head and "<thead><tr>{}</tr></thead>".format(''.join(["<th>{}</th>".format(h) for h in head])) or ''
    if footer and hasattr(footer, '__iter__'):
        foot = '<tfoot><tr>{}</tr></tfoot>'.format(''.join(["<td>{}</td>".format(f) for f in footer]))
    elif footer=='':
        foot = ''
    else:
        foot = footer or (len(alist) and "{:,d} items".format(len(alist))) or "None"
        foot = '<tfoot><tr><td colspan="{}">{}</td></tr></tfoot>'.format(len(labels),foot)
    body = body and "<tbody>{}</tbody>".format('\n'.join(body)) or ''

    if sortable:
        system.libs.add("/static/dz/tablesorter/jquery.tablesorter.js")
        system.styles.add("/static/dz/tablesorter/default/style.css")
        system.tail.add("""
    <script type="text/javascript">
        $(function(){{
          $("table.{}").tablesorter();
        }});
    </script>
        """.format(selector))

    return """
<div class="table-responsive">
  {actions}
  <table class="{classed}">
      {caption}
      {head}
      {foot}
      {body}
  </table>
</div>""".format(**locals())

