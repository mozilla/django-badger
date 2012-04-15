import logging
import re

from django.conf import settings

from django import forms
from django.db import models
from django.contrib.auth.models import User, AnonymousUser
from django.forms import CharField, Textarea, ValidationError
from django.utils.translation import ugettext as _
from django.core.validators import validate_email

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


EMAIL_SEPARATOR_RE = re.compile(r'[,;\s]+')


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


class MultiEmailField(forms.Field):
    """Form field which accepts multiple email addresses""" 
    # Based on https://docs.djangoproject.com/en/dev/ref/forms/validation/
    #          #form-field-default-cleaning
    widget = Textarea

    def __init__(self, **kwargs):
        self.max_emails = kwargs.get('max_emails', 10)
        del kwargs['max_emails']
        super(MultiEmailField, self).__init__(**kwargs)

    def to_python(self, value):
        "Normalize data to a list of strings."
        if not value:
            return []
        return EMAIL_SEPARATOR_RE.split(value)

    def validate(self, value):
        "Check if value consists only of valid emails."
        super(MultiEmailField, self).validate(value)

        # Enforce max number of email addresses
        if len(value) > self.max_emails:
            raise ValidationError(
                _('%s items entered, only %s allowed') %
                (len(value), self.max_emails))
        
        # Validate each of the addresses, 
        for email in value:
            if not email:
                continue
            try:
                validate_email(email)
            except ValidationError, e:
                raise ValidationError(_('%s is not a valid email address') %
                                      (email,))


class BadgeAwardForm(MyForm):
    """Form to create either a real or deferred badge award"""
    # TODO: Needs a captcha?
    emails = MultiEmailField(max_emails=10,
            help_text="Enter up to 10 email addresses for badge award "
                      "recipients")


class DeferredAwardGrantForm(MyForm):
    """Form to grant a deferred badge award"""
    # TODO: Needs a captcha?
    email = forms.EmailField()
