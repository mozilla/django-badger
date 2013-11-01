import logging
import re

from django.conf import settings

from django import forms
from django.db import models
from django.contrib.auth.models import User, AnonymousUser
from django.forms import FileField, CharField, Textarea, ValidationError
from django.core.validators import validate_email

try:
    from tower import ugettext_lazy as _
except ImportError:
    from django.utils.translation import ugettext_lazy as _

from badger.models import Award, Badge, Nomination

try:
    from taggit.managers import TaggableManager
except ImportError:
    TaggableManager = None


EMAIL_SEPARATOR_RE = re.compile(r'[,;\s]+')


class MyModelForm(forms.ModelForm):

    required_css_class = "required"
    error_css_class = "error"

    def as_ul(self):
        """Returns this form rendered as HTML <li>s -- excluding the <ul></ul>.
        """
        # TODO: l10n: This doesn't work for rtl languages
        return self._html_output(
            normal_row=(u'<li%(html_class_attr)s>%(label)s %(field)s'
                        '%(help_text)s%(errors)s</li>'),
            error_row=u'<li>%s</li>',
            row_ender='</li>',
            help_text_html=u' <p class="help">%s</p>',
            errors_on_separate_row=False)


class MyForm(forms.Form):

    required_css_class = "required"
    error_css_class = "error"

    def as_ul(self):
        """Returns this form rendered as HTML <li>s -- excluding the <ul></ul>.
        """
        # TODO: l10n: This doesn't work for rtl languages
        return self._html_output(
            normal_row=(u'<li%(html_class_attr)s>%(label)s %(field)s'
                        '%(help_text)s%(errors)s</li>'),
            error_row=u'<li>%s</li>',
            row_ender='</li>',
            help_text_html=u' <p class="help">%s</p>',
            errors_on_separate_row=False)


class MultipleItemsField(forms.Field):
    """Form field which accepts multiple text items"""
    # Based on https://docs.djangoproject.com/en/dev/ref/forms/validation/
    #          #form-field-default-cleaning
    widget = Textarea

    def __init__(self, **kwargs):
        self.max_items = kwargs.get('max_items', 10)
        if 'max_items' in kwargs:
            del kwargs['max_items']
        self.separator_re = re.compile(r'[,;\s]+')
        if 'separator_re' in kwargs:
            del kwargs['separator_re']
        super(MultipleItemsField, self).__init__(**kwargs)

    def to_python(self, value):
        """Normalize data to a list of strings."""
        if not value:
            return []
        items = self.separator_re.split(value)
        return [i.strip() for i in items if i.strip()]

    def validate_item(self, item):
        return True

    def validate(self, value):
        """Check if value consists only of valid items."""
        super(MultipleItemsField, self).validate(value)

        # Enforce max number of items
        if len(value) > self.max_items:
            raise ValidationError(
                _(u'{num} items entered, only {maxnum} allowed').format(
                    num=len(value), maxnum=self.max_items))

        # Validate each of the items
        invalid_items = []
        for item in value:
            try:
                self.validate_item(item)
            except ValidationError:
                invalid_items.append(item)

        if len(invalid_items) > 0:
            # TODO: l10n: Not all languages separate with commas
            raise ValidationError(
                _(u'These items were invalid: {itemlist}').format(
                    itemlist=u', '.join(invalid_items)))


class MultiEmailField(MultipleItemsField):
    """Form field which accepts multiple email addresses"""
    def validate_item(self, item):
        validate_email(item)


class BadgeAwardForm(MyForm):
    """Form to create either a real or deferred badge award"""
    # TODO: Needs a captcha?
    emails = MultiEmailField(max_items=10,
            help_text=_(u'Enter up to 10 email addresses for badge award '
                            'recipients'))
    description = CharField(
            label='Explanation',
            widget=Textarea, required=False,
            help_text=_(u'Explain why this badge should be awarded'))


class DeferredAwardGrantForm(MyForm):
    """Form to grant a deferred badge award"""
    # TODO: Needs a captcha?
    email = forms.EmailField()


class MultipleClaimCodesField(MultipleItemsField):
    """Form field which accepts multiple DeferredAward claim codes"""
    def validate_item(self, item):
        from badger.models import DeferredAward
        try:
            DeferredAward.objects.get(claim_code=item)
            return True
        except DeferredAward.DoesNotExist:
            raise ValidationError(_(u'No such claim code, {claimcode}').format(
                claimcode=item))


class DeferredAwardMultipleGrantForm(MyForm):
    email = forms.EmailField(
            help_text=_(u'Email address to which claims should be granted'))
    claim_codes = MultipleClaimCodesField(
            help_text=_(u'Comma- or space-separated list of badge claim codes'))


class BadgeEditForm(MyModelForm):

    class Meta:
        model = Badge
        fields = ('title', 'image', 'description',)
        try:
            # HACK: Add "tags" as a field only if the taggit app is available.
            import taggit
            fields += ('tags',)
        except ImportError:
            pass
        fields += ('unique', 'nominations_accepted',
                   'nominations_autoapproved',)

    required_css_class = "required"
    error_css_class = "error"

    def __init__(self, *args, **kwargs):
        super(BadgeEditForm, self).__init__(*args, **kwargs)

        # TODO: l10n: Pretty sure this doesn't work for rtl languages.
        # HACK: inject new templates into the image field, monkeypatched
        # without creating a subclass
        self.fields['image'].widget.template_with_clear = u'''
            <p class="clear">%(clear)s
                <label for="%(clear_checkbox_id)s">%(clear_checkbox_label)s</label></p>
        '''
        # TODO: l10n: Pretty sure this doesn't work for rtl languages.
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

    def __init__(self, *args, **kwargs):
        super(BadgeNewForm, self).__init__(*args, **kwargs)


class BadgeSubmitNominationForm(MyForm):
    """Form to submit badge nominations"""
    emails = MultiEmailField(max_items=10,
            help_text=_(
                u'Enter up to 10 email addresses for badge award nominees'))
