"""
Signals relating to badges.
"""
from django.dispatch import Signal


badge_will_be_awarded = Signal(providing_args=["award"])
badge_was_awarded = Signal(providing_args=["award"])
