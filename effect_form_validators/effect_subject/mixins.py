from django import forms
from edc_constants.constants import NO, NOT_APPLICABLE, YES
from edc_visit_schedule.utils import is_baseline


class ReportingFieldsetFormValidatorMixin:
    reportable_fields = ["reportable_as_ae", "patient_admitted"]

    def validate_field_na_baseline(self, field_applicable: str):
        if (
            is_baseline(self.cleaned_data.get("subject_visit"))
            and self.cleaned_data.get(field_applicable) != NOT_APPLICABLE
        ):
            raise forms.ValidationError(
                {field_applicable: "This field is not applicable at baseline."}
            )

    def validate_reporting_fieldset_na_baseline(self):
        for reportable_field in self.reportable_fields:
            self.validate_field_na_baseline(field_applicable=reportable_field)

    def validate_reporting_fieldset_applicable_if_not_baseline(self):
        for reportable_field in self.reportable_fields:
            self.applicable_if_true(
                condition=not is_baseline(self.cleaned_data.get("subject_visit")),
                field_applicable=reportable_field,
            )
