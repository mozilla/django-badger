"""
Signals relating to badges.
"""
from django.dispatch import Signal


badge_will_be_awarded = Signal(providing_args=["award"])
badge_was_awarded = Signal(providing_args=["award"])

user_will_be_nominated = Signal(providing_args=["nomination"])
user_was_nominated = Signal(providing_args=["nomination"])

nomination_will_be_approved = Signal(providing_args=["nomination"])
nomination_was_approved = Signal(providing_args=["nomination"])

nomination_will_be_accepted = Signal(providing_args=["nomination"])
nomination_was_accepted = Signal(providing_args=["nomination"])
