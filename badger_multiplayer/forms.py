import logging

from django.conf import settings

from django import forms
from django.db import models
from django.contrib.auth.models import User, AnonymousUser

try:
    from tower import ugettext_lazy as _
except ImportError, e:
    from django.utils.translation import ugettext_lazy as _

from badger.models import (Badge, Award, Nomination)


class MyModelForm(forms.ModelForm):
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
    def as_ul(self):
        "Returns this form rendered as HTML <li>s -- excluding the <ul></ul>."
        return self._html_output(
            normal_row=(u'<li%(html_class_attr)s>%(label)s %(field)s' +
                '%(help_text)s%(errors)s</li>'),
            error_row=u'<li>%s</li>',
            row_ender='</li>',
            help_text_html=u' <p class="help">%s</p>',
            errors_on_separate_row=False)


class BadgeEditForm(MyModelForm):

    class Meta:
        model = Badge
        fields = ('title', 'description',)

    required_css_class = "required"
    error_css_class = "error"


class BadgeNewForm(BadgeEditForm):

    class Meta(BadgeEditForm.Meta):
        pass
        #fields = (SubmissionEditForm.Meta.fields +
        #    ('captcha', 'accept_terms',))

    #captcha = ReCaptchaField(label=_("Show us you're human"))
    #accept_terms = forms.BooleanField(initial=False, required=True)

    def __init__(self, *args, **kwargs):
        super(BadgeNewForm, self).__init__(*args, **kwargs)
        #if not settings.RECAPTCHA_PRIVATE_KEY:
        #    del self.fields['captcha']

