"""Signals relating to badges.

For each of these, you can register to receive them using standard
Django methods.

Let's look at :py:func:`badges.signals.badge_will_be_awarded`. For
example::

    from badger.signals import badge_will_be_awarded

    @receiver(badge_will_be_awarded)
    def my_callback(sender, **kwargs):
        award = kwargs['award']

        print('sender: {0}'.format(sender))
        print('award: {0}'.format(award))


The sender will be :py:class:`badges.models.Award` class. The
``award`` argument will be the ``Award`` instance that is being
awarded.

"""
from django.dispatch import Signal


def _signal_with_docs(args, doc):
    # FIXME - this fixes the docstring, but not the provided arguments
    # so the API docs look weird.
    signal = Signal(providing_args=args)
    signal.__doc__ = doc
    return signal


badge_will_be_awarded = _signal_with_docs(
    ['award'],
    """Fires off before badge is awarded

    Signal receiver parameters:

    :arg award: the Award instance

    """)

badge_was_awarded = _signal_with_docs(
    ['award'],
    """Fires off after badge is awarded

    Signal receiver parameters:

    :arg award: the Award instance

    """)

user_will_be_nominated = _signal_with_docs(
    ['nomination'],
    """Fires off before user is nominated for a badge

    Signal receiver parameters:

    :arg nomination: the Nomination instance

    """)

user_was_nominated = _signal_with_docs(
    ['nomination'],
    """Fires off after user is nominated for a badge

    Signal receiver parameters:

    :arg nomination: the Nomination instance

    """)

nomination_will_be_approved = _signal_with_docs(
    ['nomination'],
    """Fires off before nomination is approved

    Signal receiver parameters:

    :arg nomination: the Nomination instance being approved

    """)

nomination_was_approved = _signal_with_docs(
    ['nomination'],
    """Fires off after nomination is approved

    Signal receiver parameters:

    :arg nomination: the Nomination instance being approved

    """)

nomination_will_be_accepted = _signal_with_docs(
    ['nomination'],
    """Fires off before nomination is accepted

    Signal receiver parameters:

    :arg nomination: the Nomination instance being accepted

    """)

nomination_was_accepted = _signal_with_docs(
    ['nomination'],
    """Fires off after nomination is accepted

    Signal receiver parameters:

    :arg nomination: the Nomination instance being accepted

    """)

nomination_will_be_rejected = _signal_with_docs(
    ['nomination'],
    """Fires off before nomination is rejected

    Signal receiver parameters:

    :arg nomination: the Nomination instance being rejected

    """)

nomination_was_rejected = _signal_with_docs(
    ['nomination'],
    """Fires off after nomination is rejected

    Signal receiver parameters:

    :arg nomination: the Nomination instance being rejected

    """)
