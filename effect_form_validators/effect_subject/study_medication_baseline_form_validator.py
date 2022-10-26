from edc_appointment.constants import TODAY
from edc_constants.constants import NO, NOT_APPLICABLE, YES
from edc_crf.crf_form_validator import CrfFormValidator
from edc_form_validators import INVALID_ERROR
from edc_utils.text import formatted_date
from edc_visit_schedule.utils import is_baseline


class StudyMedicationBaselineFormValidator(CrfFormValidator):
    def clean(self) -> None:
        if not is_baseline(instance=self.related_visit):
            self.raise_validation_error(
                {"__all__": "This form may only be completed at baseline"}, INVALID_ERROR
            )

        # TODO: Validate vital signs (inc weight) has already been collected

        self.validate_flucon()
        self.validate_flucyt()

    def validate_flucon(self) -> None:
        self.required_if(
            NO, field="flucon_initiated", field_required="flucon_not_initiated_reason"
        )
        self.required_if(YES, field="flucon_initiated", field_required="flucon_dose_datetime")

        if self.report_datetime and self.cleaned_data.get("flucon_dose_datetime"):
            if (
                self.report_datetime.date()
                != self.cleaned_data.get("flucon_dose_datetime").date()
            ):
                dte_as_str = formatted_date(self.report_datetime.date())
                self.raise_validation_error(
                    {"flucon_dose_datetime": f"Expected {dte_as_str}"}, INVALID_ERROR
                )

        self.required_if(
            YES,
            field="flucon_initiated",
            field_required="flucon_dose",
            field_required_evaluate_as_int=True,
        )

        self.applicable_if(YES, field="flucon_initiated", field_applicable="flucon_next_dose")

        if (
            self.cleaned_data.get("flucon_initiated") == YES
            and self.cleaned_data.get("flucon_next_dose") != TODAY
        ):
            self.raise_validation_error(
                {
                    "flucon_next_dose": (
                        "Invalid. Expected first dose at baseline to be administered today."
                    )
                },
                INVALID_ERROR,
            )

        self.required_if_true(
            condition=(
                self.cleaned_data.get("flucon_dose") is not None
                and self.cleaned_data.get("flucon_dose") != 1200
            ),
            field_required="flucon_notes",
            required_msg="Fluconazole dose not 1200 mg/d.",
            inverse=False,
        )

    def validate_flucyt(self) -> None:
        # TODO: 'flucyt_initiated' should be NA if on control arm

        self.required_if(
            NO, field="flucyt_initiated", field_required="flucyt_not_initiated_reason"
        )

        self.required_if(YES, field="flucyt_initiated", field_required="flucyt_dose_datetime")
        if self.report_datetime and self.cleaned_data.get("flucyt_dose_datetime"):
            if (
                self.report_datetime.date()
                != self.cleaned_data.get("flucyt_dose_datetime").date()
            ):
                dte_as_str = formatted_date(self.report_datetime.date())
                self.raise_validation_error(
                    {"flucyt_dose_datetime": f"Expected {dte_as_str}"}, INVALID_ERROR
                )

        # TODO: 'flucyt_dose_expected' to be calculated or validated against vital signs weight

        self.required_if(
            YES,
            field="flucyt_initiated",
            field_required="flucyt_dose",
            field_required_evaluate_as_int=True,
        )

        dose_fields = [f"flucyt_dose_{hr}" for hr in ["0400", "1000", "1600", "2200"]]
        for dose_field in dose_fields:
            self.required_if(
                YES,
                field="flucyt_initiated",
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

        self.applicable_if(YES, field="flucyt_initiated", field_applicable="flucyt_next_dose")

        if self.cleaned_data.get("flucyt_dose_datetime"):
            if (
                self.cleaned_data.get("flucyt_dose_datetime")
                < self.cleaned_data.get("flucyt_dose_datetime").replace(
                    hour=13, minute=0, second=0, microsecond=0
                )
                and self.cleaned_data.get("flucyt_next_dose") != "1000"
            ):
                self.raise_validation_error(
                    {
                        "flucyt_next_dose": (
                            "Invalid. Expected 'at 10:00' if first dose before 13:00."
                        ),
                    },
                    INVALID_ERROR,
                )
            elif (
                self.cleaned_data.get("flucyt_dose_datetime")
                >= self.cleaned_data.get("flucyt_dose_datetime").replace(
                    hour=13, minute=0, second=0, microsecond=0
                )
            ) and self.cleaned_data.get("flucyt_next_dose") != "1600":
                self.raise_validation_error(
                    {
                        "flucyt_next_dose": (
                            "Invalid. Expected 'at 16:00' if first dose on or after 13:00."
                        ),
                    },
                    INVALID_ERROR,
                )

        self.not_required_if(
            NOT_APPLICABLE,
            field="flucyt_initiated",
            field_not_required="flucyt_notes",
            inverse=False,
        )

        self.required_if_true(
            condition=(
                self.cleaned_data.get("flucyt_dose_expected") is not None
                and self.cleaned_data.get("flucyt_dose") is not None
                and self.cleaned_data.get("flucyt_dose_expected")
                != self.cleaned_data.get("flucyt_dose")
            ),
            field_required="flucyt_notes",
            required_msg="Flucytosine expected and prescribed doses differ.",
            inverse=False,
        )
