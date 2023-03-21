from edc_form_validators import FormValidator

from .missed_doses_form_validator_mixin import MissedDosesFormValidatorMixin


class FluconMissedDosesFormValidator(MissedDosesFormValidatorMixin, FormValidator):
    field = "day_missed"
    reason_field = "missed_reason"
    reason_other_field = "missed_reason_other"
    day_range = range(1, 16)

    def clean(self) -> None:
        self.validate_missed_days()
