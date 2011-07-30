## Open questions

* Are register_signals and update_badges the right idea in badges.py?

## TODO

* Nomination - create, delete, update, approve, reject

* Pagination on home badge list

* Per-user award list / trophy case

* Badge images by upload or URL
    * URL accomodates badges in code
    * Restrict base URL of images?

* Badge image upload
    * validate, scale, thumbnail, date-based filename
    * steal Demo Studio code for this?

* Activity streams - JSON and Atom

* Option in update_badges management command to overwrite existing.

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

* REST API
    * Might be better as a separate package?
