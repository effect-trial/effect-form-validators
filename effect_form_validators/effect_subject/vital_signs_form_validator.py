from edc_form_validators.form_validator import FormValidator

from .mixins import ReportingFieldsetFormValidatorMixin


class VitalSignsFormValidator(ReportingFieldsetFormValidatorMixin, FormValidator):
    def clean(self) -> None:
        self.required_if_true(True, field_required="sys_blood_pressure")
        self.required_if_true(True, field_required="dia_blood_pressure")

        self.validate_reporting_fieldset_na_baseline()
        self.validate_reporting_fieldset_applicable_if_not_baseline()
