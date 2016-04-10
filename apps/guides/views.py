"""
    guide views
"""

from zoom import page
from zoom.html import div, ul, h1
from zoom import link_to, id_for

def generate_index(toc):
    """Generate a table of contents page"""

    def toc_guide(name):
        """generate a toc entry for a guide"""
        return link_to(name, id_for(name))

    def toc_section(section):
        """generate a section header"""
        heading, reports = section
        return h1(heading) + ul(toc_guide(r) for r in reports)

    sections = toc

    return div(ul(toc_section(section) for section in sections), Class='dz-toc')


def guide(feature, side_panel, body):
    """returns a guide page"""
    layout = """
        <div class="dz-guide">
            <div class="row feature bg-info">
                <div class="col-md-9">
                    {feature}
                </div>
                <div class="col-md-3 side-panel">
                    {side_panel}
                </div>
            </div>
            <div class="row body">
                <div class="col-md-9">
                    {body}
                </div>
            </div>
        </div>
    """
    return page(layout.format(
        feature=feature,
        side_panel=side_panel,
        body=body,
    ))
