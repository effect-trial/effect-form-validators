from edc_constants.constants import YES


class EffectSubjectConsentFormValidatorMixin:
    def validate_sample_export(self):
        self.applicable_if(YES, field="sample_storage", field_applicable="sample_export")
