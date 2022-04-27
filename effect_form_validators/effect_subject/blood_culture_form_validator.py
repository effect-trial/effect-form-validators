from edc_form_validators import FormValidator
from edc_microbiology.form_validators import BloodCultureSimpleFormValidatorMixin


class BloodCultureFormValidator(
    BloodCultureSimpleFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        self.validate_blood_culture()
