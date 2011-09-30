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
from badger.forms import (MyModelForm, MyForm)
from badger_multiplayer.models import (Badge, Nomination)


class BadgeEditForm(MyModelForm):

    class Meta:
        model = Badge
        fields = ('title', 'image', 'description',)

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

class BadgeSubmitNominationForm(MyModelForm):

    class Meta:
        model = Nomination
        fields = ('nominee', )

