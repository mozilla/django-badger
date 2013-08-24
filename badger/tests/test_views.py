import logging
import hashlib

from django.conf import settings

from django.http import HttpRequest
from django.test.client import Client

from django.utils import simplejson
from django.utils.translation import get_language

from django.contrib.auth.models import User

from pyquery import PyQuery as pq

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from django.template.defaultfilters import slugify

try:
    from funfactory.urlresolvers import (get_url_prefix, Prefixer, reverse,
                                         set_url_prefix)
    from tower import activate
except ImportError:
    from django.core.urlresolvers import reverse
    get_url_prefix = None

from . import BadgerTestCase

from badger.models import (Badge, Award, Nomination, Progress, DeferredAward,
        NominationApproveNotAllowedException,
        NominationAcceptNotAllowedException,
        BadgeAwardNotAllowedException)
from badger.utils import get_badge, award_badge


class BadgerViewsTest(BadgerTestCase):

    def setUp(self):
        self.testuser = self._get_user()
        self.client = Client()
        Award.objects.all().delete()

    def tearDown(self):
        Award.objects.all().delete()
        Badge.objects.all().delete()

    @attr('json')
    def test_badge_detail(self):
        """Can view badge detail"""
        user = self._get_user()
        badge = Badge(creator=user, title="Test II",
                      description="Another test")
        badge.save()

        r = self.client.get(reverse('badger.views.detail',
            args=(badge.slug,)), follow=True)
        doc = pq(r.content)

        eq_('badge_detail', doc.find('body').attr('id'))
        eq_(1, doc.find('.badge .title:contains("%s")' % badge.title).length)
        eq_(badge.description, doc.find('.badge .description').text())

        # Now, take a look at the JSON format
        url = reverse('badger.detail_json', args=(badge.slug, ))
        r = self.client.get(url, follow=True)

        data = simplejson.loads(r.content)
        eq_(badge.title, data['name'])
        eq_(badge.description, data['description'])
        eq_('http://testserver%s' % badge.get_absolute_url(), 
            data['criteria'])

    @attr('json')
    def test_award_detail(self):
        """Can view award detail"""
        user = self._get_user()
        user2 = self._get_user(username='tester2')

        b1, created = Badge.objects.get_or_create(creator=user,
                title="Code Badge #1", description="Some description")
        award = b1.award_to(user2)

        url = reverse('badger.views.award_detail', args=(b1.slug, award.pk,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_('award_detail', doc.find('body').attr('id'))
        eq_(1, doc.find('.award .awarded_to .username:contains("%s")' % user2.username).length)
        eq_(1, doc.find('.badge .title:contains("%s")' % b1.title).length)

        # Now, take a look at the JSON format
        url = reverse('badger.award_detail_json', args=(b1.slug, award.pk,))
        r = self.client.get(url, follow=True)

        data = simplejson.loads(r.content)

        hash_salt = (hashlib.md5('%s-%s' % (award.badge.pk, award.pk))
                            .hexdigest())
        recipient_text = '%s%s' % (award.user.email, hash_salt)
        recipient_hash = ('sha256$%s' % hashlib.sha256(recipient_text)
                                               .hexdigest())

        eq_(recipient_hash, data['recipient'])
        eq_('http://testserver%s' % award.get_absolute_url(), 
            data['evidence'])
        eq_(award.badge.title, data['badge']['name'])
        eq_(award.badge.description, data['badge']['description'])
        eq_('http://testserver%s' % award.badge.get_absolute_url(), 
            data['badge']['criteria'])

    def test_awards_by_user(self):
        """Can view awards by user"""
        user = self._get_user()
        user2 = self._get_user(username='tester2')

        b1, created = Badge.objects.get_or_create(creator=user, title="Code Badge #1")
        b2, created = Badge.objects.get_or_create(creator=user, title="Code Badge #2")
        b3, created = Badge.objects.get_or_create(creator=user, title="Code Badge #3")

        b1.award_to(user2)
        award_badge(b2.slug, user2)
        Award.objects.create(badge=b3, user=user2)

        url = reverse('badger.views.awards_by_user', args=(user2.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_('badge_awards_by_user', doc.find('body').attr('id'))
        eq_(3, doc.find('.badge').length)
        for b in (b1, b2, b3):
            eq_(1, doc.find('.badge .title:contains("%s")' % b.title).length)

    def test_awards_by_badge(self):
        """Can view awards by badge"""
        user = self._get_user()
        b1 = Badge.objects.create(creator=user, title="Code Badge #1")

        u1 = self._get_user(username='tester1')
        u2 = self._get_user(username='tester2')
        u3 = self._get_user(username='tester3')

        for u in (u1, u2, u3):
            b1.award_to(u)

        url = reverse('badger.views.awards_by_badge', args=(b1.slug,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_(3, doc.find('.award').length)
        for u in (u1, u2, u3):
            eq_(1, doc.find('.award .user:contains("%s")' % u.username)
                      .length)

    def test_award_detail_includes_nomination(self):
        """Nomination should be included in award detail"""
        creator = self._get_user(username="creator", email="creator@example.com")
        awardee = self._get_user(username="awardee", email="awardee@example.com")
        nominator = self._get_user(username="nominator", email="nominator@example.com")

        b1 = Badge.objects.create(creator=creator, title="Badge to awarded")

        ok_(not b1.is_awarded_to(awardee))

        nomination = b1.nominate_for(nominator=nominator, nominee=awardee)
        nomination.approve_by(creator)
        nomination.accept(awardee)

        ok_(b1.is_awarded_to(awardee))

        award = Award.objects.get(badge=b1, user=awardee)

        r = self.client.get(award.get_absolute_url(), follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)

        nomination_el = doc.find('.award .nominated_by .username')
        eq_(nomination_el.length, 1)
        eq_(nomination_el.text(), str(nominator))

        approved_el = doc.find('.award .nomination_approved_by .username')
        eq_(approved_el.length, 1)
        eq_(approved_el.text(), str(creator))

    def test_award_detail_includes_nomination_autoapproved(self):
        """Auto-approved nomination should be indicated in award detail"""
        creator = self._get_user(username="creator", email="creator@example.com")
        awardee = self._get_user(username="awardee", email="awardee@example.com")
        nominator = self._get_user(username="nominator", email="nominator@example.com")

        b2 = Badge.objects.create(creator=creator, title="Badge to awarded 2")
        b2.nominations_autoapproved = True
        b2.save()

        ok_(not b2.is_awarded_to(awardee))

        nomination = b2.nominate_for(nominator=nominator, nominee=awardee)
        nomination.accept(awardee)

        ok_(b2.is_awarded_to(awardee))

        award = Award.objects.get(badge=b2, user=awardee)

        r = self.client.get(award.get_absolute_url(), follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)

        approved_el = doc.find('.award .nomination_approved_by .autoapproved')
        eq_(approved_el.length, 1)

    def test_issue_award(self):
        """Badge creator can issue award to another user"""
        SAMPLE_DESCRIPTION = u'This is a sample description'
        
        user1 = self._get_user(username="creator", email="creator@example.com")
        user2 = self._get_user(username="awardee", email="awardee@example.com")

        b1 = Badge.objects.create(creator=user1, title="Badge to awarded")

        url = reverse('badger.views.award_badge', args=(b1.slug,))

        # Non-creator should be denied attempt to award badge
        self.client.login(username="awardee", password="trustno1")
        r = self.client.get(url, follow=True)
        eq_(403, r.status_code)

        # But, the creator should be allowed
        self.client.login(username="creator", password="trustno1")
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        form = doc('form#award_badge')
        eq_(1, form.length)
        eq_(1, form.find('*[name=emails]').length)
        eq_(1, form.find('*[name=description]').length)
        eq_(1, form.find('input.submit,button.submit').length)

        r = self.client.post(url, dict(
            emails=user2.email,
            description=SAMPLE_DESCRIPTION
        ), follow=False)

        ok_('award' in r['Location'])

        ok_(b1.is_awarded_to(user2))

        award = Award.objects.filter(user=user2, badge=b1)[0]
        eq_(SAMPLE_DESCRIPTION, award.description)
        
        r = self.client.get(award.get_absolute_url(), follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_(SAMPLE_DESCRIPTION, doc.find('.award .description').text())

    def test_issue_multiple_awards(self):
        """Multiple emails can be submitted at once to issue awards"""
        # Build creator user and badge
        creator = self._get_user(username="creator", email="creator@example.com")
        b1 = Badge.objects.create(creator=creator, title="Badge to defer")

        # Build future awardees
        user1 = self._get_user(username="user1", email="user1@example.com")
        user2 = self._get_user(username="user2", email="user2@example.com")
        user3 = self._get_user(username="user3", email="user3@example.com")
        user4_email = 'user4@example.com'

        # Login as the badge creator, prepare to award...
        self.client.login(username="creator", password="trustno1")
        url = reverse('badger.views.award_badge', args=(b1.slug,))
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        # Make sure the expected parts appear in the form.
        doc = pq(r.content)
        form = doc('form#award_badge')
        eq_(1, form.length)
        eq_(1, form.find('*[name=emails]').length)
        eq_(1, form.find('input.submit,button.submit').length)

        # Post a list of emails with a variety of separators.
        r = self.client.post(url, dict(
            emails=("%s,%s\n%s %s" %
                    (user1.email, user2.email, user3.email, user4_email)),
        ), follow=False)

        # Ensure that the known users received awards and the unknown user got
        # a deferred award.
        ok_(b1.is_awarded_to(user1))
        ok_(b1.is_awarded_to(user2))
        ok_(b1.is_awarded_to(user3))
        eq_(1, DeferredAward.objects.filter(email=user4_email).count())

    def test_deferred_award_claim_on_login(self):
        """Ensure that a deferred award gets claimed on login."""
        deferred_email = "awardee@example.com"
        user1 = self._get_user(username="creator", email="creator@example.com")
        b1 = Badge.objects.create(creator=user1, title="Badge to defer")
        url = reverse('badger.views.award_badge', args=(b1.slug,))

        self.client.login(username="creator", password="trustno1")
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        form = doc('form#award_badge')
        eq_(1, form.length)
        eq_(1, form.find('*[name=emails]').length)
        eq_(1, form.find('input.submit,button.submit').length)

        r = self.client.post(url, dict(
            emails=deferred_email,
        ), follow=False)

        ok_('award' not in r['Location'])

        user2 = self._get_user(username="awardee", email=deferred_email)
        self.client.login(username="awardee", password="trustno1")
        r = self.client.get(reverse('badger.views.detail',
            args=(b1.slug,)), follow=True)
        ok_(b1.is_awarded_to(user2))

    def test_deferred_award_immediate_claim(self):
        """Ensure that a deferred award can be immediately claimed rather than
        viewing detail"""
        deferred_email = "awardee@example.com"
        user1 = self._get_user(username="creator", email="creator@example.com")
        b1 = Badge.objects.create(creator=user1, title="Badge to defer")
        
        da = DeferredAward(badge=b1, creator=user1)
        da.save()
        url = da.get_claim_url()

        # Just viewing the claim URL shouldn't require login.
        r = self.client.get(url, follow=False)
        eq_(200, r.status_code)

        # But, attempting to claim the award should require login
        r = self.client.post(reverse('badger.views.claim_deferred_award'), dict(
            code=da.claim_code,
        ), follow=False)
        eq_(302, r.status_code)
        ok_('login' in r['Location'])

        # So, try logging in and fetch the immediate-claim URL
        user2 = self._get_user(username="awardee", email=deferred_email)
        self.client.login(username="awardee", password="trustno1")
        r = self.client.post(reverse('badger.views.claim_deferred_award'), dict(
            code=da.claim_code,
        ), follow=False)
        eq_(302, r.status_code)
        ok_('awards' in r['Location'])

        ok_(b1.is_awarded_to(user2))

    def test_claim_code_shows_awards_after_claim(self):
        """Claim code URL should lead to award detail or list after claim"""
        user1 = self._get_user(username="creator",
                               email="creator@example.com")
        user2 = self._get_user(username="awardee",
                               email="awardee@example.com")
        b1 = Badge.objects.create(creator=user1, unique=False,
                                  title="Badge for claim viewing")
        da = DeferredAward(badge=b1, creator=user1)
        da.save()

        url = da.get_claim_url()

        # Before claim, code URL leads to claim page. 
        r = self.client.get(url, follow=False)
        eq_(200, r.status_code)
        doc = pq(r.content)
        form = doc('form#claim_award')

        # After claim, code URL leads to a single award detail page.
        award = da.claim(user2)
        r = self.client.get(url, follow=False)
        eq_(302, r.status_code)
        award_url = reverse('badger.views.award_detail',
                            args=(award.badge.slug, award.pk))
        ok_(award_url in r['Location'])

    def test_reusable_deferred_award_visit(self):
        """Issue #140: Viewing a claim page for a deferred award that has been
        claimed, yet is flagged as reusable, should result in the claim page
        and not a redirect to awards"""
        user1 = self._get_user(username="creator", email="creator@example.com")
        user2 = self._get_user(username="awardee1", email="a1@example.com")
        user3 = self._get_user(username="awardee2", email="a2@example.com")

        # Create the badge, a deferred award, and claim it once already.
        b1 = Badge.objects.create(creator=user1, title="Badge to defer")
        da = DeferredAward.objects.create(badge=b1, creator=user1,
                                          reusable=True)
        da.claim(user3)

        # Visiting the claim URL should yield the claim code page.
        url = da.get_claim_url()
        self.client.login(username="awardee1", password="trustno1")
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        form = doc('form#claim_award')
        eq_(1, form.length)

    def test_grant_deferred_award(self):
        """Deferred award for a badge can be granted to an email address."""
        deferred_email = "awardee@example.com"
        user1 = self._get_user(username="creator", email="creator@example.com")
        b1 = Badge.objects.create(creator=user1, title="Badge to defer")
        
        da = DeferredAward(badge=b1, creator=user1, email='foobar@example.com')
        da.save()
        url = da.get_claim_url()

        self.client.login(username="creator", password="trustno1")
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        form = doc('form#grant_award')
        eq_(1, form.length)
        eq_(1, form.find('*[name=email]').length)
        eq_(1, form.find('input.submit,button.submit').length)

        r = self.client.post(url, dict(
            is_grant=1, email=deferred_email,
        ), follow=False)

        user2 = self._get_user(username="awardee", email=deferred_email)
        self.client.login(username="awardee", password="trustno1")
        r = self.client.get(reverse('badger.views.detail',
            args=(b1.slug,)), follow=True)
        ok_(b1.is_awarded_to(user2))

    def test_create(self):
        """Can create badge with form"""
        # Login should be required
        r = self.client.get(reverse('badger.views.create'))
        eq_(302, r.status_code)
        ok_('/accounts/login' in r['Location'])

        # Should be fine after login
        settings.BADGER_ALLOW_ADD_BY_ANYONE = True
        self.client.login(username="tester", password="trustno1")
        r = self.client.get(reverse('badger.views.create'))
        eq_(200, r.status_code)

        # Make a chick check for expected form elements
        doc = pq(r.content)

        form = doc('form#create_badge')
        eq_(1, form.length)

        eq_(1, form.find('input[name=title]').length)
        eq_(1, form.find('textarea[name=description]').length)
        # For styling purposes, we'll allow either an input or button element
        eq_(1, form.find('input.submit,button.submit').length)

        r = self.client.post(reverse('badger.views.create'), dict(
        ), follow=True)
        doc = pq(r.content)
        eq_(1, doc.find('form .error > input[name=title]').length)

        badge_title = "Test badge #1"
        badge_desc = "This is a test badge"

        r = self.client.post(reverse('badger.views.create'), dict(
            title=badge_title,
            description=badge_desc,
        ), follow=True)
        doc = pq(r.content)

        eq_('badge_detail', doc.find('body').attr('id'))
        ok_(badge_title in doc.find('.badge .title').text())
        eq_(badge_desc, doc.find('.badge .description').text())

        slug = doc.find('.badge').attr('data-slug')

        badge = Badge.objects.get(slug=slug)
        eq_(badge_title, badge.title)
        eq_(badge_desc, badge.description)

    def test_edit(self):
        """Can edit badge detail"""
        user = self._get_user()
        badge = Badge(creator=user, title="Test II",
                      description="Another test")
        badge.save()

        self.client.login(username="tester", password="trustno1")

        r = self.client.get(reverse('badger.views.detail',
            args=(badge.slug,)), follow=True)
        doc = pq(r.content)

        eq_('badge_detail', doc.find('body').attr('id'))
        edit_url = doc.find('a.edit_badge').attr('href')
        ok_(edit_url is not None)

        r = self.client.get(edit_url)
        doc = pq(r.content)
        eq_('badge_edit', doc.find('body').attr('id'))

        badge_title = "Edited title"
        badge_desc = "Edited description"

        r = self.client.post(edit_url, dict(
            title=badge_title,
            description=badge_desc,
        ), follow=True)
        doc = pq(r.content)

        eq_('badge_detail', doc.find('body').attr('id'))
        ok_(badge_title in doc.find('.badge .title').text())
        eq_(badge_desc, doc.find('.badge .description').text())

        slug = doc.find('.badge').attr('data-slug')

        badge = Badge.objects.get(slug=slug)
        eq_(badge_title, badge.title)
        eq_(badge_desc, badge.description)

    def test_edit_preserves_creator(self):
        """Edit preserves the original creator of the badge (bugfix)"""
        orig_user = self._get_user(username='orig_user')
        badge = Badge(creator=orig_user, title="Test 3",
                      description="Another test")
        badge.save()

        edit_user = self._get_user(username='edit_user')
        edit_user.is_superuser = True
        edit_user.save()

        self.client.login(username="edit_user", password="trustno1")
        edit_url = reverse('badger.views.edit',
                args=(badge.slug,))
        r = self.client.post(edit_url, dict(
            title='New Title',
        ), follow=True)
        doc = pq(r.content)

        # The badge's creator should not have changed to the editing user.
        badge_after = Badge.objects.get(pk=badge.pk)
        ok_(badge_after.creator.pk != edit_user.pk)

    def test_delete(self):
        """Can delete badge"""
        user = self._get_user()
        badge = Badge(creator=user, title="Test III",
                      description="Another test")
        badge.save()
        slug = badge.slug

        badge.award_to(user)

        self.client.login(username="tester", password="trustno1")

        r = self.client.get(reverse('badger.views.detail',
            args=(badge.slug,)), follow=True)
        doc = pq(r.content)

        eq_('badge_detail', doc.find('body').attr('id'))
        delete_url = doc.find('a.delete_badge').attr('href')
        ok_(delete_url is not None)

        r = self.client.get(delete_url)
        doc = pq(r.content)
        eq_('badge_delete', doc.find('body').attr('id'))
        eq_("1", doc.find('.awards_count').text())

        r = self.client.post(delete_url, {}, follow=True)
        doc = pq(r.content)

        try:
            badge = Badge.objects.get(slug=slug)
            ok_(False)
        except Badge.DoesNotExist:
            ok_(True)

    def test_delete_award(self):
        """Can delete award"""
        user = self._get_user()
        badge = Badge(creator=user, title="Test III",
                      description="Another test")
        badge.save()

        award = badge.award_to(user)

        self.client.login(username="tester", password="trustno1")

        r = self.client.get(reverse('badger.views.award_detail',
            args=(badge.slug, award.id)), follow=True)
        doc = pq(r.content)

        eq_('award_detail', doc.find('body').attr('id'))
        delete_url = doc.find('a.delete_award').attr('href')
        ok_(delete_url is not None)

        r = self.client.post(delete_url, {}, follow=True)

        try:
            award = Award.objects.get(pk=award.pk)
            ok_(False)
        except Award.DoesNotExist:
            ok_(True)

    def _get_user(self, username="tester", email="tester@example.com",
            password="trustno1"):
        (user, created) = User.objects.get_or_create(username=username,
                defaults=dict(email=email))
        if created:
            user.set_password(password)
            user.save()
        return user
