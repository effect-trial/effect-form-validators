from edc_constants.constants import YES
from edc_form_validators.form_validator import FormValidator


class HospitalizationFormValidator(FormValidator):
    def clean(self):

        self.required_if(YES, field="discharged", field_required="discharged_date")
        self.applicable_if(
            YES, field="discharged", field_applicable="discharged_date_estimated"
        )

        self.required_if(YES, field="lp_performed", field_required="lp_count")

        self.required_if(YES, field="have_details", field_required="narrative", inverse=False)
