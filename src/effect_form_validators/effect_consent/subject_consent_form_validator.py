from edc_consent.form_validators import SubjectConsentFormValidatorMixin
from edc_form_validators import FormValidator

from ..form_validator_mixins import EffectSubjectConsentFormValidatorMixin


class SubjectConsentFormValidator(
    EffectSubjectConsentFormValidatorMixin,
    SubjectConsentFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        self.validate_sample_export()
