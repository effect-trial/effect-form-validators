from edc_constants.constants import NO, OTHER, YES
from edc_crf.crf_form_validator import CrfFormValidator
from effect_lists.constants import STEROIDS


class PatientHistoryFormValidator(CrfFormValidator):
    def _clean(self) -> None:
        self.validate_flucon()

        self.required_if(
            YES, field="reported_neuro_abnormality", field_required="neuro_abnormality_details"
        )

        self.validate_tb()

        self.required_if(YES, field="previous_oi", field_required="previous_oi_name")
        self.required_if(YES, field="previous_oi", field_required="previous_oi_date")

        self.validate_other_medication()

    def validate_flucon(self):
        self.required_if(YES, field="flucon_1w_prior_rando", field_required="flucon_days")
        self.applicable_if(YES, field="flucon_1w_prior_rando", field_applicable="flucon_dose")
        self.validate_other_specify(field="flucon_dose")
        self.required_if(OTHER, field="flucon_dose", field_required="flucon_dose_other_reason")

    def validate_tb(self):
        self.applicable_if(YES, field="tb_prev_dx", field_applicable="tb_site")
        self.applicable_if(YES, field="tb_prev_dx", field_applicable="on_tb_tx")
        self.applicable_if(NO, field="on_tb_tx", field_applicable="tb_dx_ago")
        self.applicable_if(YES, field="on_tb_tx", field_applicable="on_rifampicin")
        self.required_if(YES, field="on_rifampicin", field_required="rifampicin_start_date")
        self.validate_date_against_report_datetime("rifampicin_start_date")

    def validate_other_medication(self):
        self.m2m_applicable_if(YES, field="any_medications", m2m_field="specify_medications")
        self.m2m_other_specify(
            STEROIDS, m2m_field="specify_medications", field_other="specify_steroid_other"
        )
        self.m2m_other_specify(
            OTHER, m2m_field="specify_medications", field_other="specify_medications_other"
        )
