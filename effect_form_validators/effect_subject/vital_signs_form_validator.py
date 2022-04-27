from edc_form_validators.form_validator import FormValidator
from edc_visit_schedule.utils import is_baseline


class VitalSignsFormValidator(FormValidator):
    def clean(self) -> None:
        self.required_if_true(True, field_required="sys_blood_pressure")
        self.required_if_true(True, field_required="dia_blood_pressure")
        for fld in ["reportable_as_ae", "patient_admitted"]:
            self.applicable_if_true(
                condition=not is_baseline(self.cleaned_data.get("subject_visit")),
                field_applicable=fld,
                not_applicable_msg="This field is not applicable at baseline",
            )
