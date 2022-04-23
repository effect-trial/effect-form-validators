from edc_constants.constants import NORMAL, OTHER, YES
from edc_form_validators import INVALID_ERROR
from edc_form_validators.form_validator import FormValidator


class ChestXrayFormValidator(FormValidator):
    def clean(self):

        self.validate_against_ssx()

        self.required_if(YES, field="chest_xray", field_required="chest_xray_date")

        self.m2m_required_if(YES, field="chest_xray", m2m_field="chest_xray_results")

        self.m2m_single_selection_if(NORMAL, m2m_field="chest_xray_results")

        self.m2m_other_specify(
            OTHER,
            m2m_field="chest_xray_results",
            field_other="chest_xray_results_other",
        )

    def validate_against_ssx(self):
        xray_performed = getattr(
            self.cleaned_data.get("subject_visit").signsandsymptoms,
            "xray_performed",
            None,
        )
        if (
            xray_performed
            and self.cleaned_data.get("chest_xray")
            and self.cleaned_data.get("chest_xray") != xray_performed
        ):
            raise self.raise_validation_error(
                {"chest_xray": "Invalid. X-ray not performed. See `Signs and Symptoms`"},
                INVALID_ERROR,
            )
