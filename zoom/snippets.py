

import tools
from store import store, Entity

class Snippet(Entity):
    """
    A chunk of text (usually HTML) that can be rendered by
    placing the <dz:snippet> tag in a document or template.

        >>> from system import system
        >>> system.setup_test()
        >>> for s in snippets.find(name='test'): s.delete()
        >>> snippets.find(name='test')
        []

        >>> t = snippets.put(Snippet(name='test', body='some text'))
        >>> snippets.find(name='test')
        [<Snippet {'name': 'test', 'body': 'some text'}>]

    """
    pass

snippets = store(Snippet)

def snippet(name, variant=None, default='', markdown=False):
    snippet = snippets.first(name=name, variant=variant)
    if snippet:
        snippet['impressions'] = snippet.get('impressions', 0) + 1
        snippets.put(snippet)
        result = snippet.body
    else:
        result = default
    if markdown:
        return tools.markdown(result)
    else:
        return result


