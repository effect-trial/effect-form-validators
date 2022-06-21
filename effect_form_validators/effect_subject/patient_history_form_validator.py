from edc_constants.constants import NO, OTHER, YES
from edc_crf.crf_form_validator import CrfFormValidator


class PatientHistoryFormValidator(CrfFormValidator):
    def _clean(self) -> None:
        self.validate_flucon()

        # TODO neuro_abnormality_details required if reported_neuro_abnormality

        self.validate_tb()

        # TODO: previous_oi_name required if previous_oi
        # TODO: previous_oi_dx_date required if previous_oi

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
        pass
        # TODO: specify_medications required if any_medications
        # TODO: specify_medications NA behaviour???
        # TODO: specify_steroid_other required if specify_medications == Steroids
        # TODO: specify_medications_other required if specify_medications == Other
