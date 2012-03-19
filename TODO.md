## TODO

### Core

* Award by email address
    * Find an existing user
    * If no existing user, create an invite code to defer award
        * Need to revive the invite code notion

* Allow users to ignore, reject, delete, hide awards

* Dump / disable / comment out in-house badge OBI baking in favor of
  outsourcing to openbadges.org

* Thumbnail sizing on image uploads for badges and profile avatars

* Search-driven badge awarding (rather than drop down)

* user-managed trophycase(s)
    * multiple user-curated display sets of awards
    * needs a decent printable stylesheet to make lanyards
    * QR code built-in?

* Get more Hypermedia API flavor
    * Accept: application/json along with .json extension
    * Start accepting POSTs, PUTs, and DELETEs for programmatic manipulation.

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

* Update README for django-badger with docs and more description of features

* Tags on badges?

* Busybox game demo that exercises badge progress, metabadges, etc.

* design help needed
    * overall layout and UI
    * visual cues for badge vs user vs award

* CSS layout broken on clean slate front page
* CSS tweaks for long display names
    * restrict display name length a bit more?

### Multiplayer

* Badge properties
    * No self-nominations
    * Auto-approve all nominations
    * Expires after x time
    * Accept nominations from anyone
    * Auto-approve all nominations

* Nomination
    * Reject
    * Second / Like

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

* Hypermedia API
    * Sprinkle in some more JSON and honor Accept: application/json
    * Accept programmatic writes
    * OAuth for machines as alternate to BrowserID for people

### Misc

* Test out the new Vanilla django templates from phoebebright
    * At least build an example django app around them

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

## Open questions

* Are register_signals and update_badges the right idea in badges.py?

