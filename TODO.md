## Open questions

* Are register_signals and update_badges the right idea in badges.py?

## TODO

### Inbox

* Tags on badges?
* Search-driven badge awarding (rather than drop down)
* List approval-pending nominations for user (home page?)
* List acceptance-pending nominations for user (home page?)

### Core

* Comments on badges, awards
* Badge expiration datetime
* Notifications
    * Email? Inbox on site? Other channel?
    * Accept nominations from anyone
    * Auto-approve all nominations
    * Awards available to claim
    * not central to django-badger
    * badge awards can be caught with signal subscriptions
    * but, should it still be up to a project to handle that?
* Templates
    * jinja helpers
    * django templatetags?
* Activity streams - JSON and Atom
    * Re-work feeds to be AS compliant
* Option in update_badges management command to overwrite existing.

### Multiplayer

* Nomination - create, delete, update, approve, reject
* Badge delegates
    * List of users managed by badge creator who can
        * Issue awards
        * Approve nominations
* Conditional nominations
    * Models
        * Condition definition
        * Uplift more logic into progress model
* Badge properties
    * Auto-approve all nominations
    * Expires after x time
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

### Misc

* Badge deletion
    * Disallow if awards have been issued; require all awards be revoked first
* Captchas?
    * On nomination submit, award issue forms
* Localization of badges in DB?
    * django-modeltranslation - http://code.google.com/p/django-modeltranslation/
        * Adds per-locale columns to existing model
    * transdb - http://code.google.com/p/transdb/
        * Needs modification / subclass of model
        * Adds a blob column with JSON structure containing translations
