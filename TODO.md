## TODO

* Permissions

* Nomination - create, delete, update, approve, reject

* Per-user award list

* Badge image upload
    * validate, scale, thumbnail, date-based filename
    * steal Demo Studio code for this?

* Conditional nominations
    * Auto-approved when a condition met
    * Models
        * Condition definition
        * Per-user status tracking
    * Examples
        * Progress counter
        * Badge set completion

* Define initial badges in app/{name}/badges.py
    * Includes signals to hook award/nomination conditions up to model activity 
    * Register initial set of conditional nominations
    * Should still be able to manage images, etc, in admin / database

* Activity streams - JSON and Atom

* REST API
    * Might be better as a separate package?

* Notifications? (not central to django-badger)

* Pagination on home badge list

* Nomination with claim code
    * Claim optionally triggers approval
    * Could be expressed as QR code

* How much of this can be loosely-coupled through signals?
