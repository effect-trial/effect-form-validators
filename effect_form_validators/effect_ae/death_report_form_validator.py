from edc_adverse_event.form_validators import DeathReportFormValidator as FormValidator
from edc_constants.constants import YES


class DeathReportFormValidator(FormValidator):
    def clean(self):
        cleaned_data = super().clean()
        self.validate_hospitalization()
        self.validate_nok()
        return cleaned_data

    def validate_hospitalization(self):
        self.required_if(
            YES, field="death_as_inpatient", field_required="hospitalization_date"
        )

        self.date_is_before_or_raise(
            field="hospitalization_date",
            reference_value=self.death_report_date,
            inclusive=True,
            extra_msg="(on or before date of death)",
        )

        self.applicable_if(
            YES, field="death_as_inpatient", field_applicable="hospitalization_date_estimated"
        )
        self.applicable_if(
            YES, field="death_as_inpatient", field_applicable="clinical_notes_available"
        )
        self.applicable_if(YES, field="clinical_notes_available", field_applicable="cm_sx")

    def validate_nok(self):
        self.required_if(YES, field="speak_nok", field_required="date_first_unwell")

        self.date_is_before_or_raise(
            field="date_first_unwell",
            reference_value=self.death_report_date,
            inclusive=True,
            extra_msg="(on or before date of death)",
        )

        self.date_is_before_or_raise(
            field="date_first_unwell",
            reference_value=self.cleaned_data.get("hospitalization_date"),
            inclusive=True,
            extra_msg="(on or before date of hospitalization)",
        )

        for fld in [
            "date_first_unwell_estimated",
            "headache",
            "drowsy_confused_altered_behaviour",
            "seizures",
            "blurred_vision",
        ]:
            self.applicable_if(YES, field="speak_nok", field_applicable=fld)

        self.required_if(YES, field="speak_nok", field_required="nok_narrative")
