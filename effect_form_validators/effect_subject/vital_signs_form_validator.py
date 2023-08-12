from edc_constants.constants import YES
from edc_crf.crf_form_validator import CrfFormValidator
from edc_form_validators import INVALID_ERROR
from edc_vitals import has_severe_htn
from edc_vitals.form_validators import BloodPressureFormValidatorMixin
from edc_vitals.utils import (
    get_dia_upper,
    get_g3_fever_lower,
    get_sys_upper,
    has_g3_fever,
    has_g4_fever,
)


class VitalSignsFormValidator(BloodPressureFormValidatorMixin, CrfFormValidator):
    def clean(self) -> None:
        self.required_if_true(True, field_required="sys_blood_pressure")

        self.required_if_true(True, field_required="dia_blood_pressure")

        self.raise_on_systolic_lt_diastolic_bp(**self.cleaned_data)

        self.validate_reporting_fieldset()

    def validate_reporting_fieldset(self):
        self.applicable_if_true(True, field_applicable="reportable_as_ae")
        if self.cleaned_data.get("reportable_as_ae") != YES and has_severe_htn(
            sys=self.cleaned_data.get("sys_blood_pressure"),
            dia=self.cleaned_data.get("dia_blood_pressure"),
        ):
            self.raise_validation_error(
                message={
                    "reportable_as_ae": (
                        "Invalid. Expected YES. "
                        "Participant has severe hypertension "
                        f"(BP reading >= {get_sys_upper()}/{get_dia_upper()}mmHg)."
                    )
                },
                error_code=INVALID_ERROR,
            )

        if self.cleaned_data.get("reportable_as_ae") != YES and (
            has_g3_fever(temperature=self.cleaned_data.get("temperature"))
            or has_g4_fever(temperature=self.cleaned_data.get("temperature"))
        ):
            self.raise_validation_error(
                message={
                    "reportable_as_ae": (
                        "Invalid. Expected YES. "
                        "Participant has G3 or higher fever "
                        f"(temperature >= {get_g3_fever_lower()})."
                    )
                },
                error_code=INVALID_ERROR,
            )
        self.applicable_if_true(True, field_applicable="patient_admitted")
