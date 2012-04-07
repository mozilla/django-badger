## TODO

### Core

* Claim codes
    * Reusable claim code management for badge owner
        * Tool to mass-generate single-use claim codes
        * Page to list all self-owned deferred awards for a badge
            * Printable stylesheet, make easily cut-out physical claim tickets
    * Expiration time on DeferredAward
        * reusables should self-destruct after the end-time of an event
    * "Giftable" claim code
        * Allows someone with access to the claim code to process it on behalf
          of someone else.
          * e.g. Registration desk with net access at an event. Hand over the
            code, registration worker visits claim URL, enters email address of
            claimant. Claimant gets the award.
        * With reusable deferred award: Enter an email address, clone the
          deferred award as a single-use assigned to the given email.
        * With a single-use: Enter an email address and assign it to the
          deferred award. Blank out or regenerate the claim code.

* user-managed trophycase(s)
    * multiple user-curated display sets of awards
    * needs a decent printable stylesheet to make lanyards
    * QR code built-in?
    * maybe just outsource this to openbadges.org
        * combine award acceptance in Badger with a subsequent JS call to OBI
          issuing API.
        * Can it be iframe'd into the profile page?

* Tags for badges?
    * Geeky, but hashtags are in popular use now
    * Data visualization on badge tag page
        * how many awards per badge, maybe some nice pie charts
        * who's being awarded?
        * who's authored badges?

* Update to work with OBI changes
    * Use salty hashes instead of email addresses
    * Dump / disable / comment out in-house badge OBI baking in favor of
      outsourcing to openbadges.org

* Fix sign-in immediately after sign-out
    * Seems like the CSRF token in the session gets dumped, which makes the
      sign-in button broken

* Subdomains
    * Origin for umbrella issuer, based on user or group?
    * Useful for an event?

* Update vanilla django templates

* Award description / explanation field

* Nomination description / explanation field

* Allow users to ignore, reject, delete, hide awards

* Thumbnail sizing on image uploads for badges and profile avatars

* Search-driven badge awarding (rather than drop down)

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

* Busybox game demo that exercises badge progress, metabadges, etc.

* design help needed
    * overall layout and UI
    * visual cues for badge vs user vs award

### Multiplayer

* Nominate by email address, instead of user selection

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

