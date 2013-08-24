#!/usr/bin/env python
"""Quick and dirty render-to-PDF for badge award claim codes"""

import logging
import math
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
from reportlab.platypus.doctemplate import LayoutError
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize 
from reportlab.lib.units import inch 
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from reportlab.lib import textsplit

from reportlab.lib.utils import ImageReader

from django.conf import settings

from django.http import (HttpResponseRedirect, HttpResponse,
        HttpResponseForbidden, HttpResponseNotFound)

from django.utils.html import conditional_escape


def render_claims_to_pdf(request, slug, claim_group, deferred_awards):
    """Currently hard-coded to print to Avery 22805 labels"""

    metrics = dict(
        page_width=(8.5 * inch),
        page_height=(11.0 * inch),

        top_margin=(0.5 * inch),
        left_margin=((25.0 / 32.0) * inch),

        qr_overlap=((1.0 / 32.0) * inch),
        padding=((1.0 / 16.0) * inch),

        horizontal_spacing=((5.0 / 16.0) * inch),
        vertical_spacing=((13.0 / 64.0) * inch),

        width=(1.5 * inch),
        height=(1.5 * inch),
    )

    debug = (request.GET.get('debug', False) is not False)

    pagesize = (metrics['page_width'], metrics['page_height'])
    cols = int((metrics['page_width'] - metrics['left_margin']) /
               (metrics['width'] + metrics['horizontal_spacing']))
    rows = int((metrics['page_height'] - metrics['top_margin']) /
               (metrics['height'] + metrics['vertical_spacing']))
    per_page = (cols * rows)
    label_ct = len(deferred_awards)
    page_ct = math.ceil(label_ct / per_page)

    pages = [deferred_awards[x:x + (per_page)]
             for x in range(0, label_ct, per_page)]

    response = HttpResponse(content_type='application/pdf; charset=utf-8')
    if not debug:
        # If debugging, don't force download.
        response['Content-Disposition'] = ('attachment; filename="%s-%s.pdf"' %
                (slug.encode('utf-8', 'replace'), claim_group))

    badge_img = None

    fout = StringIO()
    c = canvas.Canvas(fout, pagesize=pagesize)

    for page in pages:
        c.translate(metrics['left_margin'],
                    metrics['page_height'] - metrics['top_margin'])

        for row in range(0, rows, 1):
            c.translate(0.0, 0 - metrics['height'])
            c.saveState()

            for col in range(0, cols, 1):

                try:
                    da = page.pop(0)
                except IndexError:
                    continue

                if not badge_img:
                    image_fin = da.badge.image.file
                    image_fin.open()
                    badge_img = ImageReader(StringIO(image_fin.read()))

                c.saveState()
                render_label(request, c, metrics, da, badge_img, debug)
                c.restoreState()

                dx = (metrics['width'] + metrics['horizontal_spacing'])
                c.translate(dx, 0.0)

            c.restoreState()
            c.translate(0.0, 0 - metrics['vertical_spacing'])

        c.showPage()

    c.save()
    response.write(fout.getvalue())
    return response


def render_label(request, c, metrics, da, badge_img, debug):
    """Render a single label"""
    badge = da.badge

    badge_image_width = (1.0 + (1.0 / 64.0)) * inch
    badge_image_height = (1.0 + (1.0 / 64.0)) * inch

    qr_left = badge_image_width - metrics['qr_overlap']
    qr_bottom = badge_image_height - metrics['qr_overlap']
    qr_width = metrics['width'] - qr_left
    qr_height = metrics['height'] - qr_bottom

    if False and debug:
        # Draw some layout lines on debug.
        c.setLineWidth(0.3)
        c.rect(0, 0, metrics['width'], metrics['height'])
        c.rect(qr_left, qr_bottom, qr_width, qr_height)
        c.rect(0, 0, badge_image_width, badge_image_height)

    fit_text(c, da.badge.title,
             0.0, badge_image_height,
             badge_image_width, qr_height)

    c.saveState()
    c.rotate(-90)

    code_height = qr_height * (0.45)
    claim_height = qr_height - code_height

    c.setFont("Courier", code_height)
    c.drawCentredString(0 - (badge_image_width / 2.0),
                        metrics['height'] - code_height,
                        da.claim_code)

    text = """
        <font name="Helvetica">Claim at</font> <font name="Courier">%s</font>
    """ % (settings.SITE_TITLE)
    fit_text(c, text,
             0 - badge_image_height, badge_image_width,
             badge_image_width, claim_height)

    c.restoreState()

    # Attempt to build a QR code image for the claim URL
    claim_url = request.build_absolute_uri(da.get_claim_url())
    qr_img = None
    try:
        # Try using PyQRNative: http://code.google.com/p/pyqrnative/
        # badg.us should have this in vendor-local
        from PyQRNative import QRCode, QRErrorCorrectLevel
        # TODO: Good-enough settings?
        if len(claim_url) < 20:
            qr = QRCode(3, QRErrorCorrectLevel.L)
        elif len(claim_url) < 50:
            qr = QRCode(4, QRErrorCorrectLevel.L)
        else:
            qr = QRCode(10, QRErrorCorrectLevel.L)
        qr.addData(claim_url)
        qr.make()
        qr_img = ImageReader(qr.makeImage())

    except ImportError:
        try:
            # Hmm, if we don't have PyQRNative, then try abusing this web
            # service. Should be fine for low volumes.
            qr_url = ("http://api.qrserver.com/v1/create-qr-code/?%s" %
                urllib.urlencode({'size': '%sx%s' % (500, 500),
                                  'data': claim_url}))

            qr_img = ImageReader(StringIO(urllib2.urlopen(qr_url).read()))

        except Exception:
            # Ignore issues in drawing the QR code - maybe show an error?
            pass

    if qr_img:
        c.drawImage(qr_img, qr_left, qr_bottom, qr_width, qr_height)

    c.drawImage(badge_img,
                0.0 * inch, 0.0 * inch,
                badge_image_width, badge_image_height)


def fit_text(c, text, x, y, max_w, max_h, font_name='Helvetica',
             padding_w=4.5, padding_h=4.5, font_decrement=0.0625):
    """Draw text, reducing font size until it fits with a given max width and
    height."""

    max_w -= (padding_w * 2.0)
    max_h -= (padding_h * 2.0)

    x += padding_w
    y += padding_h

    font_size = max_h

    while font_size > 1.0:
        ps = ParagraphStyle(name='text', alignment=TA_CENTER,
                            fontName=font_name, fontSize=font_size,
                            leading=font_size)
        p = Paragraph(text, ps)
        actual_w, actual_h = p.wrapOn(c, max_w, max_h)
        if actual_h > max_h or actual_w > max_w:
            font_size -= font_decrement
        else:
            y_pad = (max_h - actual_h) / 2
            p.drawOn(c, x, y + y_pad)
            return
