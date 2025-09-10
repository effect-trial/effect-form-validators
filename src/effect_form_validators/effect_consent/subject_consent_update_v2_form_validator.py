from __future__ import annotations

from edc_form_validators.form_validator import FormValidator

from ..form_validator_mixins import EffectSubjectConsentFormValidatorMixin


class SubjectConsentUpdateV2FormValidator(
    EffectSubjectConsentFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        self.validate_sample_export()
