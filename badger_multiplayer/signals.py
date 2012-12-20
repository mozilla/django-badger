"""
Signals relating to badges.
"""
from django.dispatch import Signal


user_will_be_nominated = Signal(providing_args=["nomination"])
user_was_nominated = Signal(providing_args=["nomination"])

nomination_will_be_approved = Signal(providing_args=["nomination"])
nomination_was_approved = Signal(providing_args=["nomination"])

nomination_will_be_accepted = Signal(providing_args=["nomination"])
nomination_was_accepted = Signal(providing_args=["nomination"])
