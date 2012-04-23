#!/usr/bin/env python
"""Quick and dirty render-to-PDF for badge award claim codes"""

import logging
import urllib
import urllib2
try:
    from cStringIO import cStringIO as StringIO
except ImportError:
    from StringIO import StringIO

from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, BaseDocTemplate, Paragraph, Preformatted, Spacer,
    PageBreak, Frame, FrameBreak, PageTemplate, Image, Table)
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
top_margin = (0.5 * inch)
left_margin = (0.1875 * inch)
width = 2.52 * inch
height = 1.0 * inch
vertical_spacing = 0 * inch
horizontal_spacing = 0.10 * inch
columns = 3
rows = 10


def render_claims_to_pdf(request, slug, claim_group, deferred_awards):
    debug = (request.GET.get('debug', False) is not False)

    response = HttpResponse(content_type='application/pdf; charset=utf-8')
    if not debug:
        # If debugging, don't force download.
        response['Content-Disposition'] = ('attachment; filename="%s-%s.pdf"' %
                (slug.encode('utf-8', 'replace'), claim_group))

    doc = BaseDocTemplate(response, pageSize=pagesizes.letter,
            topMargin=top_margin, leftMargin=left_margin,
            allowSplitting=1)
    
    if debug: show_boundary = 1
    else: show_boundary = 0

    # Build frames for labels in the template
    frames = []
    for r_idx in range(0, rows):
        for c_idx in range(0, columns):
            frames.append(Frame(
                left_margin + (c_idx * (width + horizontal_spacing)),
                doc.height - (r_idx * (height + vertical_spacing)),
                width, height,
                leftPadding=0, rightPadding=0,
                bottomPadding=0, topPadding=0,
                showBoundary=show_boundary
            ))

    # Add the template to the page.
    template = PageTemplate(frames=frames)
    doc.addPageTemplates(template)

    # Build some common styles
    style = ParagraphStyle(name='normal', alignment=TA_CENTER,
        fontName='Helvetica', fontSize=9, leading=9)
    code_style = ParagraphStyle(name='code', alignment=TA_CENTER,
        fontName='Courier', fontSize=9.5, leading=9.5)

    # Fill out the template with claim codes.
    items = []
    for da in deferred_awards:
        badge = da.badge
        award_url = request.build_absolute_uri(da.get_claim_url())

        badge_img = StringIO(badge.image.file.read())

        # TODO: Stop abusing the Google Charts API and get our own QR code
        # baking on premises.
        try:
            qr_url = ("http://chart.apis.google.com/chart?%s" %
                urllib.urlencode({'chs':'%sx%s' % (250, 250), 
                                  'cht':'qr', 'chl':award_url, 'choe':'UTF-8'}))
            qr_img = StringIO(urllib2.urlopen(qr_url).read())
        except Exception, e:
            return HttpResponse('QR code generation failed: %s' % e,
                                status=500)

        # Build the badge label out as a table...
        table_data = (
            (
                Image(badge_img, 0.6 * inch, 0.6 * inch),
                Image(qr_img, 0.6 * inch, 0.6 * inch)
            ),
            (
                # Use resize_para to shrink the font size as title gets longer.
                resize_para(badge.title),
                (
                    resize_para(request.build_absolute_uri('/'),
                                max_width=0.85 * inch),
                    Paragraph(da.claim_code.upper(), code_style),
                )
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

    return response


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
