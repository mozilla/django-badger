## Open questions

* Are register_signals and update_badges the right idea in badges.py?

## TODO

* BUG: Caching is too aggressive on demo site
* Set up BrowserID on demo site
* Upgrade demo site to post-funfactory playdoh
* Implement nominations
* Implement straight multiplayer award creation
* Add images to Badge and Award feeds

### Core

* Badge expiration datetime
* Notifications
    * Email? Inbox on site? Other channel?
    * Awards available to claim
* Templates
    * jinja helpers
    * django templatetags?
* Activity streams - JSON and Atom
    * Re-work feeds to be AS compliant
* Come up with some templates that aren't totally ugly
* Option in update_badges management command to overwrite existing.

### Multiplayer

* Nomination - create, delete, update, approve, reject
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

* Notifications? 
    * not central to django-badger
    * badge awards can be caught with signal subscriptions
    * but, should it still be up to a project to handle that?
* Localization of badges in DB?
    * django-modeltranslation - http://code.google.com/p/django-modeltranslation/
        * Adds per-locale columns to existing model
    * transdb - http://code.google.com/p/transdb/
        * Needs modification / subclass of model
        * Adds a blob column with JSON structure containing translations
