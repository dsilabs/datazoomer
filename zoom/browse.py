
from helpers import link_to, url_for, name_for
from system import system
from request import route
from tools import unisafe

def browse(items, labels=None, columns=None, fields=None, footer=None, on_click=None, on_delete=None, on_remove=None, *args, **keywords):

    def trash_can(key,kind,action,**args):
        link  = url_for(str(key),action,**args)
        tpl = '<td width=1px><a href="%(link)s"><img src="/themes/%(theme)s/images/%(kind)s.png" border=0 height=13px width=13px alt="%(kind)s"></a></td>'
        return tpl % dict(link=link, kind=kind, theme=system.theme)

    def getcol(item, name):
        try:
            return item[name]
        except:
            return ''

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
                    raise Exception('%s' % hasattr(items[0],'__len__'))
                raise Exception('Unable to infer columns')

    columns = list(columns)
    labels = list(labels)

    if fields:
        #labels = []
        lookup = fields.as_dict()
        for col in columns[len(labels):]:
            if col in lookup:
                label = lookup[col].label
            else:
                label = col
            labels.append(label)

        alist = []
        for item in items:
            fields.update(item)
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

    odd_rowclass = 'dark'
    evn_rowclass = 'light'

    t = []
    if labels:
        t.append( '<tr>' )

        colnum = 0
        for label in labels:
            colnum += 1
            t.append('<th>%s</th>' % label)

        if on_delete:
            t.append('<th colwidth=1px>%s</th>' % '')
        if on_remove:
            t.append('<th colwidth=1px>%s</th>' % '')
        t.append( '</tr>' )
        odd_rowclass = 'light' # if there is a header start line shading on 2nd line
        evn_rowclass = 'dark'

    count = 0
    for row in alist:
        count += 1
        if count % 2:
            rowclass = odd_rowclass
        else:
            rowclass = evn_rowclass
        t.append( '<tr class=%s>' % rowclass )

        colnum = 0
        for item in row:
            #wrapping = len(unicode(item)) < 40 and 'nowrap' or ''
            wrapping = len(unisafe(item)) < 80 and '<td nowrap>%s</td>' or '<td>%s</td>'
            if (on_click or on_delete or on_remove) and colnum == 0:
                key = item
            if on_click and (colnum == 1 or colnum==0 and len(row)==1):
                url = '/'.join(route[1:]+[str(key)])
                #t.append('<td>%s</td>' % link_to(item, url, *args, **keywords))
                t.append(wrapping % link_to(item, url, *args, **keywords))
            elif colnum>0 or not (on_click or on_remove or on_delete):
                #t.append('<td %s>%s</td>' % (wrapping, item))
                t.append(wrapping % unisafe(item))
            colnum += 1

        if on_delete:
            t.append(trash_can(key,'delete',on_delete))

        if on_remove:
            t.append(trash_can(key,'remove',on_remove))

        t.append( '</tr>' )

    if not count:
        t.append('<tr><td colspan=%s>None</td></tr>' % len(labels))

    footer_body = footer and ('<div class="baselist-footer">%s</div>' % footer) or ''

    result = '\n'.join(['<div class="baselist"><table>'] + t + ['</table></div>'] + [footer_body])
    return result


