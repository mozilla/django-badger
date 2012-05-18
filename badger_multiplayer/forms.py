import logging

from django.conf import settings

from django import forms
from django.db import models
from django.contrib.auth.models import User, AnonymousUser
from django.forms.fields import FileField
from django.forms.widgets import ClearableFileInput

try:
    from tower import ugettext_lazy as _
except ImportError, e:
    from django.utils.translation import ugettext_lazy as _

from badger.models import (Award)
from badger.forms import (MyModelForm, MyForm, MultiEmailField)
from badger_multiplayer.models import (Badge, Nomination)

try:
    from taggit.managers import TaggableManager
except:
    TaggableManager = None


class BadgeEditForm(MyModelForm):

    class Meta:
        model = Badge
        fields = ('title', 'image', 'description', 'tags', 'unique',
                  'nominations_accepted',)

    required_css_class = "required"
    error_css_class = "error"

    def __init__(self, *args, **kwargs):
        super(BadgeEditForm, self).__init__(*args, **kwargs)

        # HACK: inject new templates into the image field, monkeypatched
        # without creating a subclass
        self.fields['image'].widget.template_with_clear = u'''
            <p class="clear">%(clear)s
                <label for="%(clear_checkbox_id)s">%(clear_checkbox_label)s</label></p>
        '''
        self.fields['image'].widget.template_with_initial = u'''
            <div class="clearablefileinput">
                <p>%(initial_text)s: %(initial)s</p>
                %(clear_template)s
                <p>%(input_text)s: %(input)s</p>
            </div>
        '''


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


class BadgeSubmitNominationForm(MyForm):
    """Form to submit badge nominations"""
    emails = MultiEmailField(max_emails=10,
            help_text="Enter up to 10 email addresses for badge award "
                      "nominees")
