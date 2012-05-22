#!/usr/bin/env python
"""Quick and dirty render-to-PDF for badge award claim codes"""

import logging
import urllib
import urllib2
try:
    from cStringIO import cStringIO as StringIO
except ImportError:
    from StringIO import StringIO

from reportlab.lib import pagesizes
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, BaseDocTemplate, Paragraph, Preformatted, Spacer,
    PageBreak, Frame, FrameBreak, PageTemplate, Image, Table)
from reportlab.platypus.doctemplate import LayoutError
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize 
from reportlab.lib.units import inch 
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors

from django.http import (HttpResponseRedirect, HttpResponse,
        HttpResponseForbidden, HttpResponseNotFound)

from django.utils.html import conditional_escape


# Constants hard-coded to print onto Avery 5630 or Avery 5260 labels
# TODO: Make formats / templates switchable
top_margin = 0.5 * inch
bottom_margin = 0.5 * inch
left_margin = 0.1875 * inch
right_margin = 0.1875 * inch
width = 2.625 * inch
height = 1.0 * inch
vertical_spacing = 0 * inch
horizontal_spacing = 0.125 * inch
columns = 3
rows = 10
page_size = (8.5 * inch, 11.0 * inch)


def render_claims_to_pdf(request, slug, claim_group, deferred_awards):
    debug = (request.GET.get('debug', False) is not False)

    response = HttpResponse(content_type='application/pdf; charset=utf-8')
    if not debug:
        # If debugging, don't force download.
        response['Content-Disposition'] = ('attachment; filename="%s-%s.pdf"' %
                (slug.encode('utf-8', 'replace'), claim_group))

    # HACK: If layout fails, it's most likely because of the title.  I am so
    # ashamed of this, but this reduces the size of badge image and title by 5%
    # for each error, until the error goes away. For the love of Bob, fix this
    # good & proper.
    scale_factor = 1.0
    while scale_factor > 0.1:
        try:
            fout = StringIO()
            _real_render(request, fout, slug, claim_group, deferred_awards,
                         debug, scale_factor)
            break
        except LayoutError, e:
            scale_factor -= 0.05

    response.write(fout.getvalue())
    return response


def _real_render(request, stream, slug, claim_group, deferred_awards, debug,
                 scale_factor=1.0):
    """Render the pages of badge codes."""
    doc = BaseDocTemplate(stream, topMargin=0, bottomMargin=0,
                          leftMargin=0, rightMargin=0, allowSplitting=0)
    
    if debug: show_boundary = 1
    else: show_boundary = 0

    # Build frames for labels in the template
    frames = []
    for r_idx in range(0, rows):
        for c_idx in range(0, columns):
            left_pos = left_margin + (c_idx * (width + horizontal_spacing))
            top_pos = (top_margin + (r_idx * (height + vertical_spacing)))
            frames.append(Frame(
                left_pos, top_pos, width, height,
                leftPadding=0, rightPadding=0,
                bottomPadding=0, topPadding=0,
                showBoundary=show_boundary
            ))

    # Add the template to the page.
    template = PageTemplate(pagesize=page_size, frames=frames)
    doc.addPageTemplates(template)

    # Fill out the template with claim codes.
    items = []
    for da in deferred_awards:
        badge = da.badge
        award_url = request.build_absolute_uri(da.get_claim_url())

        image_fin = badge.image.file
        image_fin.open()
        badge_img = StringIO(image_fin.read())

        # TODO: Stop abusing the Google Charts API and get our own QR code
        # baking on premises.
        try:
            qr_url = ("http://api.qrserver.com/v1/create-qr-code/?%s" %
                urllib.urlencode({'size':'%sx%s' % (250, 250), 
                                  'data':award_url}))
            qr_img = StringIO(urllib2.urlopen(qr_url).read())
        except Exception, e:
            return HttpResponse('QR code generation failed: %s' % e,
                                status=500)

        # Build the badge label out as a table...
        table_data = (
            (
                (
                    Image(badge_img, 0.75 * inch * scale_factor, 0.75 * inch * scale_factor),
                    resize_para(badge.title, max_width=1.75 * inch * scale_factor),
                ),
                (
                    Image(qr_img, 0.6 * inch, 0.6 * inch),
                    Paragraph(request.build_absolute_uri('/'), ParagraphStyle(
                        name='normal', alignment=TA_CENTER,
                        fontName='Helvetica', fontSize=8, leading=8)),
                    Paragraph(da.claim_code.upper(), ParagraphStyle(
                        name='code', alignment=TA_CENTER,
                        fontName='Courier', fontSize=11, leading=11)),
                ),
            ),
        )

        table_style = (
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),  
        )

        if debug:
            table_style = table_style + (
                ('GRID', (0,0), (-1,-1), 1, colors.black),  
            )

        items.append(Table(table_data, style=table_style))
        items.append(FrameBreak())

    doc.build(items)


def resize_para(str, max_size=10.0, min_size=2.0, max_width=(1.25*inch),
                font_name='Helvetica', alignment=TA_CENTER):
    """Produce a paragraph, reducing font size until it fits in the max width"""
    size = max_size
    while size > min_size:
        # HACK: Use a preformatted object so that minWidth() fomes up with
        # non-wrapped width. This just feels so dirty, dirty, but it works
        style = ParagraphStyle(name='Size %s' % size,
                               alignment=alignment, fontName=font_name,
                               fontSize=size, leading=size+0.25)
        para = Preformatted(str, style)
        if para.minWidth() <= max_width:
            para = Paragraph(str, style)
            break
        size -= 0.125
    return para
