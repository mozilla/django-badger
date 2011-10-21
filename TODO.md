## Open questions

* Are register_signals and update_badges the right idea in badges.py?

## TODO

### Inbox

* design help needed
    * overall layout and UI
    * visual cues for badge vs user vs award

* Update README for django-badger with docs and more description of features
* Thumbnail sizing on image uploads for badges and profile avatars
* Search-driven badge awarding (rather than drop down)

* CSS layout broken on clean slate front page
* CSS tweaks for long display names
    * restrict display name length a bit more?

### Core

* Allow users to reject, delete, hide awards

* Notifications
    * Email? Inbox on site? Other channel?
    * not central to django-badger
    * badge awards can be caught with signal subscriptions
    * but, should it still be up to a project to handle that?

* user-managed trophycase(s)
    * multiple user-curated display sets of awards
    * needs a decent printable stylesheet to make lanyards
    * QR code built-in?

* Tags on badges?

* Templates
    * jinja helpers
    * django templatetags?

* Activity streams - JSON and Atom
    * Re-work feeds to be AS compliant

* Option in update_badges management command to overwrite existing.

* More badge attributes
    * Expiration datetime
    * Unique per person
    * Unique across site
    * Secret info accessible only by badge awardee
        * ie. containing an amazon gift code (bad idea?)
    * Redeemable badges
        * ie. I owe you a beer
        * QR code scannable by badge owner to confirm redeeming

### Multiplayer

* Badge properties
    * No self-nominations
    * Auto-approve all nominations
    * Expires after x time
    * Accept nominations from anyone
    * Auto-approve all nominations

* Nomination
    * Reject
    * Second

* Comments on badges, awards, nominations

* Help wanted
    * Maybe a django app separate from Badger altogether
    * Flag a content object and certain fields as in need of help
    * Search by content type (eg. text, image)
    * Description of help desired (eg. design, review, rewrite, delegation)
    * Accept help and apply changes

* Badge delegates
    * List of users managed by badge creator who can
        * Issue awards
        * Approve nominations

* Conditional nominations
    * Models
        * Condition definition
        * Uplift more logic into progress model

* User badge preferences
    * User requires nominations first instead of auto-awards, so she has a
      change to approve/disapprove the award.

* Permissions

* Site-wide permissions and preferences
    * Open vs closed badge creation
    * Open vs closed badge award nomination

* Nomination with claim code
    * Claim optionally triggers approval
    * Could be expressed as QR code

### API

* REST API
    * Might be better as a separate package?
    * Most of the readable API will be covered by {json,rss,atom} feeds

### Misc

* Collapse multiple awards on a profile into a single item with a counter
* Badge deletion
    * Disallow if awards have been issued; require all awards be revoked first
* Captchas?
    * On nomination submit, award issue forms
* l10n
    * lots and lots of strings not marked up for l10n
* Localization of badges in DB?
    * django-modeltranslation - http://code.google.com/p/django-modeltranslation/
        * Adds per-locale columns to existing model
    * transdb - http://code.google.com/p/transdb/
        * Needs modification / subclass of model
        * Adds a blob column with JSON structure containing translations
