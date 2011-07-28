## Open questions

* Are register_signals and update_badges the right idea in badges.py?

## TODO

* Define initial badges in app/{name}/badges.py
    * Includes signals to hook award/nomination conditions up to model activity 
    * Register initial set of conditional nominations
    * Should still be able to manage images, etc, in admin / database

* Badge images by upload or URL
    * URL accomodates badges in code
    * Restrict base URL of images?

* Conditional nominations
    * Auto-approved when a condition met
    * Models
        * Condition definition
        * Per-user status tracking
    * Examples
        * Progress counter
        * Badge set completion

* Permissions

* Nomination - create, delete, update, approve, reject

* Per-user award list

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

* How much of this can be loosely-coupled through signals?

* Localization of badges in DB?
    * django-modeltranslation - http://code.google.com/p/django-modeltranslation/
        * Adds per-locale columns to existing model
    * transdb - http://code.google.com/p/transdb/
        * Needs modification / subclass of model
        * Adds a blob column with JSON structure containing translations

