from edc_constants.constants import NO, NOT_APPLICABLE, OTHER, PER_PROTOCOL, YES
from edc_crf.crf_form_validator import CrfFormValidator
from edc_form_validators import INVALID_ERROR
from edc_utils.text import formatted_date
from edc_visit_schedule.utils import is_baseline


class StudyMedicationFollowupFormValidator(CrfFormValidator):
    def clean(self) -> None:
        if is_baseline(instance=self.related_visit):
            self.raise_validation_error(
                {"__all__": "This form may not be completed at baseline"}, INVALID_ERROR
            )

        self.validate_modifications()
        self.validate_flucon()
        self.validate_flucyt()

    def validate_modifications(self) -> None:
        self.m2m_required_if(YES, field="modifications", m2m_field="modifications_reason")

        self.m2m_single_selection_if(PER_PROTOCOL, m2m_field="modifications_reason")

        self.m2m_other_specify(
            OTHER,
            m2m_field="modifications_reason",
            field_other="modifications_reason_other",
        )

        if (
            self.cleaned_data.get("modifications") == YES
            and self.cleaned_data.get("flucon_modified") != YES
            and self.cleaned_data.get("flucyt_modified") != YES
        ):
            error_msg = (
                "Invalid. "
                "Expected at least one modification in 'Fluconazole' or 'Flucytosine' section."
            )
            self.raise_validation_error(
                {fld: error_msg for fld in ["flucon_modified", "flucyt_modified"]},
                INVALID_ERROR,
            )

    def validate_flucon(self):
        self.not_applicable_if(
            NO,
            field="modifications",
            field_applicable="flucon_modified",
            inverse=False,
        )

        self.required_if(YES, field="flucon_modified", field_required="flucon_dose_datetime")
        if self.report_datetime and self.cleaned_data.get("flucon_dose_datetime"):
            # TODO: what are we trying to check/prevent here? Is this right?
            if self.report_datetime > self.cleaned_data.get("flucon_dose_datetime"):
                self.raise_validation_error(
                    {"flucon_dose_datetime": "Cannot be after report datetime"}, INVALID_ERROR
                )

        self.required_if(
            YES,
            field="flucon_modified",
            field_required="flucon_dose",
            field_required_evaluate_as_int=True,
        )
        # TODO: Validate dose against visit/protocol, if differs, require flucon_notes
        #   - differs could be not modified, or modified to value not expected

        self.applicable_if(YES, field="flucon_modified", field_applicable="flucon_next_dose")

        self.not_required_if(
            NOT_APPLICABLE,
            field="flucon_modified",
            field_not_required="flucon_notes",
            inverse=False,
        )

    def validate_flucyt(self):
        # TODO: 'flucyt_modified' should be NA if on control arm
        # TODO: 'flucyt_modified' should be NA > 15 days if on intervention arm
        self.not_applicable_if(
            NO,
            field="modifications",
            field_applicable="flucyt_modified",
            inverse=False,
        )

        self.required_if(YES, field="flucyt_modified", field_required="flucyt_dose_datetime")
        if self.report_datetime and self.cleaned_data.get("flucyt_dose_datetime"):
            # TODO: what are we trying to check/prevent here? Is this right?
            if (
                self.report_datetime.date()
                > self.cleaned_data.get("flucyt_dose_datetime").date()
            ):
                dte_as_str = formatted_date(self.report_datetime.date())
                self.raise_validation_error(
                    {"flucyt_dose_datetime": f"Expected {dte_as_str}"}, INVALID_ERROR
                )

        self.required_if(
            YES,
            field="flucyt_modified",
            field_required="flucyt_dose",
            field_required_evaluate_as_int=True,
        )

        dose_fields = [f"flucyt_dose_{hr}" for hr in ["0400", "1000", "1600", "2200"]]
        for dose_field in dose_fields:
            self.required_if(
                YES,
                field="flucyt_modified",
                field_required=dose_field,
                field_required_evaluate_as_int=True,
            )

        if self.cleaned_data.get("flucyt_dose") is not None:
            if sum(
                self.cleaned_data.get(fld)
                for fld in dose_fields
                if self.cleaned_data.get(fld) is not None
            ) != self.cleaned_data.get("flucyt_dose"):
                error_msg = (
                    "Invalid. "
                    "Expected sum of individual doses to match prescribed flucytosine "
                    f"dose ({self.cleaned_data.get('flucyt_dose')} mg/d)."
                )
                self.raise_validation_error(
                    {fld: error_msg for fld in dose_fields}, INVALID_ERROR
                )

        # TODO: Validate dose against visit/protocol, if differs, require flucyt_notes
        #   - differs could be not modified, or modified to value not expected

        self.applicable_if(YES, field="flucyt_modified", field_applicable="flucyt_next_dose")

        self.not_required_if(
            NOT_APPLICABLE,
            field="flucyt_modified",
            field_not_required="flucyt_notes",
            inverse=False,
        )
