from edc_constants.constants import NO, YES
from edc_crf.crf_form_validator import CrfFormValidator


class MedicalHistoryFormValidator(CrfFormValidator):
    def _clean(self) -> None:
        self.applicable_if(YES, field="tb_prev_dx", field_applicable="tb_site")
        self.applicable_if(YES, field="tb_prev_dx", field_applicable="on_tb_tx")
        self.applicable_if(NO, field="on_tb_tx", field_applicable="tb_dx_ago")
        self.applicable_if(YES, field="on_tb_tx", field_applicable="on_rifampicin")
        self.required_if(YES, field="on_rifampicin", field_required="rifampicin_start_date")
        self.validate_date_against_report_datetime("rifampicin_start_date")
