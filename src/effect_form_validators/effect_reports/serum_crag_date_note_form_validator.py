from edc_constants.constants import CONFIRMED
from edc_crf.crf_form_validator_mixins import BaseFormValidatorMixin
from edc_form_validators import INVALID_ERROR, FormValidator
from edc_registration import get_registered_subject_model_cls
from edc_screening.utils import get_subject_screening_model_cls
from edc_sites.form_validator_mixin import SiteFormValidatorMixin


class SerumCragDateNoteFormValidator(
    BaseFormValidatorMixin,
    SiteFormValidatorMixin,
    FormValidator,
):
    def clean(self):
        self.validate_serum_crag_date()

        self.validate_status()

        self.required_if_true(
            self.cleaned_data.get("status") != CONFIRMED, field_required="note"
        )

    @property
    def eligibility_date(self):
        return self.subject_screening.eligibility_datetime.date()

    @property
    def subject_screening(self):
        registered_subject = get_registered_subject_model_cls().objects.get(
            subject_identifier=self.subject_identifier
        )
        return get_subject_screening_model_cls().objects.get(
            screening_identifier=registered_subject.screening_identifier
        )

    def validate_serum_crag_date(self):
        if self.cleaned_data.get("serum_crag_date"):
            if self.cleaned_data.get("serum_crag_date") > self.eligibility_date:
                raise self.raise_validation_error(
                    {
                        "serum_crag_date": (
                            "Invalid. Cannot be after date participant became eligible."
                        )
                    },
                    INVALID_ERROR,
                )
            elif (self.eligibility_date - self.cleaned_data.get("serum_crag_date")).days > 180:
                raise self.raise_validation_error(
                    {
                        "serum_crag_date": (
                            "Invalid. Cannot be more than 180 days before screening."
                        )
                    },
                    INVALID_ERROR,
                )

        self.date_before_report_datetime_or_raise(field="serum_crag_date", inclusive=True)

    def validate_status(self):
        if (
            self.cleaned_data.get("serum_crag_date")
            and self.cleaned_data.get("status") != CONFIRMED
        ):
            raise self.raise_validation_error(
                {
                    "status": (
                        "Invalid. Expected `Confirmed / Done` if Serum CrAg date recorded."
                    )
                },
                INVALID_ERROR,
            )
        elif (
            not self.cleaned_data.get("serum_crag_date")
            and self.cleaned_data.get("status") == CONFIRMED
        ):
            raise self.raise_validation_error(
                {
                    "status": (
                        "Invalid. "
                        "Cannot be `Confirmed / Done` if Serum CrAg date not recorded."
                    )
                },
                INVALID_ERROR,
            )
