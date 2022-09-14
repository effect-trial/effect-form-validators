from edc_constants.constants import NO, YES
from edc_crf.crf_form_validator import CrfFormValidator
from edc_form_validators import INVALID_ERROR
from edc_utils.text import formatted_date
from edc_visit_schedule.utils import is_baseline


class StudyMedicationBaselineFormValidator(CrfFormValidator):
    def clean(self) -> None:
        if not is_baseline(instance=self.subject_visit):
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

        if self.cleaned_data.get("report_datetime") and self.cleaned_data.get(
            "flucon_dose_datetime"
        ):
            if (
                self.cleaned_data.get("report_datetime").date()
                != self.cleaned_data.get("flucon_dose_datetime").date()
            ):
                dte_as_str = formatted_date(self.cleaned_data.get("report_datetime").date())
                self.raise_validation_error(
                    {"flucon_dose_datetime": f"Expected {dte_as_str}"}, INVALID_ERROR
                )

        self.required_if(
            YES,
            field="flucon_initiated",
            field_required="flucon_dose_rx",
            field_required_evaluate_as_int=True,
        )

        self.required_if_true(
            condition=(
                self.cleaned_data.get("flucon_dose_rx") is not None
                and self.cleaned_data.get("flucon_dose_rx") != 1200
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
        if self.cleaned_data.get("report_datetime") and self.cleaned_data.get(
            "flucyt_dose_datetime"
        ):
            if (
                self.cleaned_data.get("report_datetime").date()
                != self.cleaned_data.get("flucyt_dose_datetime").date()
            ):
                dte_as_str = formatted_date(self.cleaned_data.get("report_datetime").date())
                self.raise_validation_error(
                    {"flucyt_dose_datetime": f"Expected {dte_as_str}"}, INVALID_ERROR
                )

        # TODO: 'flucyt_dose_expected' to be calculated or validated against vital signs weight

        self.required_if(
            YES,
            field="flucyt_initiated",
            field_required="flucyt_dose_rx",
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

        if self.cleaned_data.get("flucyt_dose_rx") is not None:
            if sum(
                self.cleaned_data.get(fld)
                for fld in dose_fields
                if self.cleaned_data.get(fld) is not None
            ) != self.cleaned_data.get("flucyt_dose_rx"):
                error_msg = (
                    "Invalid. "
                    "Expected sum of individual doses to match prescribed flucytosine "
                    f"dose ({self.cleaned_data.get('flucyt_dose_rx')} mg/d)."
                )
                self.raise_validation_error(
                    {fld: error_msg for fld in dose_fields}, INVALID_ERROR
                )

        self.required_if_true(
            condition=(
                self.cleaned_data.get("flucyt_dose_expected") is not None
                and self.cleaned_data.get("flucyt_dose_rx") is not None
                and self.cleaned_data.get("flucyt_dose_expected")
                != self.cleaned_data.get("flucyt_dose_rx")
            ),
            field_required="flucyt_notes",
            required_msg="Flucytosine expected and prescribed doses differ.",
            inverse=False,
        )
        # TODO: 'flucyt_notes' NA if 'flucyt_initiated' == NA
