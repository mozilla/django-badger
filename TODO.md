## Open questions

* Are register_signals and update_badges the right idea in badges.py?

## TODO

* Conditional nominations
    * Models
        * Condition definition
        * Uplift more logic into progress model

* Badge images by upload or URL
    * URL accomodates badges in code
    * Restrict base URL of images?

* Option in update_badges management command to overwrite existing.

* Permissions

* Nomination - create, delete, update, approve, reject

* Badge properties
    * Approve all nominations
    * Expires after x time

* User badge preferences
    * User requires nominations first instead of auto-awards, so she has a
      change to approve/disapprove the award.

* Per-user award list / trophy case

* Badge image upload
    * validate, scale, thumbnail, date-based filename
    * steal Demo Studio code for this?

* Activity streams - JSON and Atom

* REST API
    * Might be better as a separate package?

* Notifications? (not central to django-badger)

* Pagination on home badge list

* Nomination with claim code
    * Claim optionally triggers approval
    * Could be expressed as QR code

* Localization of badges in DB?
    * django-modeltranslation - http://code.google.com/p/django-modeltranslation/
        * Adds per-locale columns to existing model
    * transdb - http://code.google.com/p/transdb/
        * Needs modification / subclass of model
        * Adds a blob column with JSON structure containing translations

