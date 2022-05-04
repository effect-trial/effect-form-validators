from zoneinfo import ZoneInfo

from arrow import Arrow
from django.conf import settings
from edc_constants.constants import NO, YES
from edc_form_validators import INVALID_ERROR, FormValidator
from edc_registration import get_registered_subject_model_cls


class MedicalHistoryFormValidator(FormValidator):
    def _clean(self) -> None:
        self.applicable_if(YES, field="tb_prev_dx", field_applicable="tb_site")
        self.applicable_if(YES, field="tb_prev_dx", field_applicable="on_tb_tx")
        self.applicable_if(NO, field="on_tb_tx", field_applicable="tb_dx_ago")
        self.applicable_if(YES, field="on_tb_tx", field_applicable="on_rifampicin")
        self.required_if(NO, field="on_rifampicin", field_required="rifampicin_start_date")
        self.validate_hiv_diagnosis()

    def validate_hiv_diagnosis(self):
        if self.cleaned_data.get("report_datetime") and self.cleaned_data.get("hiv_dx_date"):
            if (
                self.cleaned_data.get("hiv_dx_date")
                > self.cleaned_data.get("report_datetime").date()
            ):
                self.raise_validation_error(
                    {"hiv_dx_date": "Invalid. Cannot be after report date"}, INVALID_ERROR
                )
            if (
                self.cleaned_data.get("hiv_dx_date")
                == self.cleaned_data.get("report_datetime").date()
                and self.cleaned_data.get("new_hiv_dx") != YES
            ):
                self.raise_validation_error(
                    {
                        "new_hiv_dx": (
                            "Invalid. This is a new HIV diagnosis. "
                            "Date matches the report date"
                        )
                    },
                    INVALID_ERROR,
                )

            screening_datetime = (
                get_registered_subject_model_cls()
                .objects.get(
                    subject_identifier=self.cleaned_data.get(
                        "subject_visit"
                    ).subject_identifier
                )
                .screening_datetime
            )
            screening_datetime_local = Arrow.fromdatetime(screening_datetime).to(
                ZoneInfo(settings.TIME_ZONE)
            )
            if (
                self.cleaned_data.get("hiv_dx_date") >= screening_datetime_local.date()
                and self.cleaned_data.get("new_hiv_dx") != YES
            ):
                self.raise_validation_error(
                    {
                        "new_hiv_dx": (
                            "Invalid. This is a new HIV diagnosis. "
                            "Date is after screening date"
                        )
                    },
                    INVALID_ERROR,
                )
