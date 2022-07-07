# TODO: Remove/switch to edc-vitals after next edc release (>=0.3.94)
from django.conf import settings


def has_g3_fever(temperature=None):
    if temperature is not None:
        return get_g3_fever_lower() <= temperature < get_g4_fever_lower()
    return None


def has_g4_fever(temperature=None):
    if temperature is not None:
        return temperature >= get_g4_fever_lower()
    return None


def get_g3_fever_lower():
    return getattr(settings, "EDC_VITALS_G3_FEVER_LOWER", 39.3)


def get_g4_fever_lower():
    return getattr(settings, "EDC_VITALS_G4_FEVER_LOWER", 40.0)
