from edc_constants.constants import CONTROL
from edc_form_validators import FormValidator
from edc_randomization.utils import (
    get_assignment_description_for_subject,
    get_assignment_for_subject,
)

from .missed_doses_form_validator_mixin import MissedDosesFormValidatorMixin


class FlucytMissedDosesFormValidator(MissedDosesFormValidatorMixin, FormValidator):
    field = "day_missed"
    reason_field = "missed_reason"
    reason_other_field = "missed_reason_other"
    day_range = range(1, 16)

    def clean(self) -> None:
        self.validate_against_study_arm()

        field_value = self.cleaned_data.get(self.field)
        self.required_if_true(
            condition=field_value in self.day_range, field_required="doses_missed"
        )

        self.validate_missed_days()

    def validate_against_study_arm(self):
        assignment = get_assignment_for_subject(
            subject_identifier=self.cleaned_data.get("adherence").subject_identifier,
            randomizer_name="default",
        )
        assignment_description = get_assignment_description_for_subject(
            subject_identifier=self.cleaned_data.get("adherence").subject_identifier,
            randomizer_name="default",
        )

        self.not_required_if_true(
            assignment == CONTROL,
            field=self.field,
            msg=f"Participant is on {CONTROL} arm ({assignment_description}).",
        )
