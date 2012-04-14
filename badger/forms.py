import logging

from django.conf import settings

from django import forms
from django.db import models
from django.contrib.auth.models import User, AnonymousUser

try:
    from tower import ugettext_lazy as _
except ImportError, e:
    from django.utils.translation import ugettext_lazy as _

from badger.models import (Award)

# TODO: Is there an extensible way to do this, where "add-ons" introduce proxy
# model objects?
try:
    from badger_multiplayer.models import Badge
except ImportError:
    from badger.models import Badge


class MyModelForm(forms.ModelForm):

    required_css_class = "required"
    error_css_class = "error"

    def as_ul(self):
        "Returns this form rendered as HTML <li>s -- excluding the <ul></ul>."
        return self._html_output(
            normal_row=(u'<li%(html_class_attr)s>%(label)s %(field)s' +
                '%(help_text)s%(errors)s</li>'),
            error_row=u'<li>%s</li>',
            row_ender='</li>',
            help_text_html=u' <p class="help">%s</p>',
            errors_on_separate_row=False)


class MyForm(forms.Form):

    required_css_class = "required"
    error_css_class = "error"

    def as_ul(self):
        "Returns this form rendered as HTML <li>s -- excluding the <ul></ul>."
        return self._html_output(
            normal_row=(u'<li%(html_class_attr)s>%(label)s %(field)s' +
                '%(help_text)s%(errors)s</li>'),
            error_row=u'<li>%s</li>',
            row_ender='</li>',
            help_text_html=u' <p class="help">%s</p>',
            errors_on_separate_row=False)


class BadgeAwardForm(MyForm):
    """Form to create either a real or deferred badge award"""
    # TODO: Needs a captcha?
    email = forms.EmailField()


class DeferredAwardGrantForm(MyForm):
    """Form to grant a deferred badge award"""
    # TODO: Needs a captcha?
    email = forms.EmailField()
