from edc_crf.crf_form_validator import CrfFormValidator
from edc_glucose.form_validators import GlucoseFormValidatorMixin


class ArvTreatmentFormValidator(GlucoseFormValidatorMixin, CrfFormValidator):
    pass
