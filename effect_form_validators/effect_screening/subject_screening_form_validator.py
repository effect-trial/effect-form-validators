from __future__ import annotations

from django import forms
from edc_constants.constants import (
    FEMALE,
    MALE,
    NO,
    NOT_APPLICABLE,
    OTHER,
    PENDING,
    POS,
    YES,
)
from edc_form_validators import FormValidator
from edc_prn.modelform_mixins import PrnFormValidatorMixin
from edc_screening.form_validator_mixins import SubjectScreeningFormValidatorMixin
from edc_utils.date import to_local


class SubjectScreeningFormValidator(
    SubjectScreeningFormValidatorMixin,
    PrnFormValidatorMixin,
    FormValidator,
):
    def clean(self) -> None:
        self.get_consent_for_period_or_raise()
        self.validate_age()
        self.validate_hiv()
        self.validate_cd4()
        self.validate_serum_crag()
        self.validate_lp_and_csf_crag()
        self.validate_cm_in_csf()
        self.validate_mg_ssx()
        self.validate_pregnancy()
        self.validate_suitability_for_study()

    @property
    def age_in_years(self) -> int | None:
        return self.cleaned_data.get("age_in_years")

    def validate_hiv(self):
        self.required_if(
            YES,
            field="hiv_pos",
            field_required="hiv_confirmed_date",
        )
        self.applicable_if(YES, field="hiv_pos", field_applicable="hiv_confirmed_method")

    def validate_cd4(self) -> None:
        if self.cleaned_data.get("cd4_date") and self.report_datetime:
            if self.cleaned_data.get("cd4_date") > to_local(self.report_datetime).date():
                raise forms.ValidationError(
                    {"cd4_date": "Invalid. Cannot be after report date"}
                )
            if (
                to_local(self.report_datetime).date() - self.cleaned_data.get("cd4_date")
            ).days > 21:
                raise forms.ValidationError(
                    {
                        "cd4_date": (
                            "Invalid. Cannot be more than 21 days before the report date"
                        )
                    }
                )

    def validate_serum_crag(self) -> None:
        """Assert serum CrAg is positive, and serum CrAg date is:
        - not before CD4 date
        - within 21 days of CD4
        """
        if self.cleaned_data.get("serum_crag_value") != POS:
            raise forms.ValidationError(
                {
                    "serum_crag_value": (
                        "Invalid. Subject must have positive serum/plasma CrAg test result."
                    )
                }
            )

        if self.cleaned_data.get("serum_crag_date") and self.cleaned_data.get("cd4_date"):
            days = (
                self.cleaned_data.get("cd4_date") - self.cleaned_data.get("serum_crag_date")
            ).days

            if days > 0:
                raise forms.ValidationError(
                    {"serum_crag_date": "Invalid. Cannot be before CD4 date."}
                )
            if not 0 <= abs(days) <= 21:
                days = (
                    self.cleaned_data.get("serum_crag_date")
                    - self.cleaned_data.get("cd4_date")
                ).days
                raise forms.ValidationError(
                    {
                        "serum_crag_date": (
                            "Invalid. Must have been performed within 21 days "
                            f"of CD4. Got {days}."
                        )
                    }
                )

    def validate_lp_and_csf_crag(self) -> None:
        self.required_if(YES, field="lp_done", field_required="lp_date")

        if self.cleaned_data.get("lp_date") and self.cleaned_data.get("serum_crag_date"):
            days = (
                self.cleaned_data.get("serum_crag_date") - self.cleaned_data.get("lp_date")
            ).days

            if days > 3:
                raise forms.ValidationError(
                    {
                        "lp_date": "Invalid. "
                        "LP cannot be more than 3 days before serum/plasma CrAg date"
                    }
                )

        if (
            self.report_datetime
            and self.cleaned_data.get("lp_date")
            and self.cleaned_data.get("lp_date") > to_local(self.report_datetime).date()
        ):
            raise forms.ValidationError({"lp_date": "Invalid. Cannot be after report date"})

        self.applicable_if(NO, field="lp_done", field_applicable="lp_declined")

        self.applicable_if(YES, field="lp_done", field_applicable="csf_crag_value")

    def validate_cm_in_csf(self) -> None:
        self.applicable_if(YES, field="lp_done", field_applicable="cm_in_csf")
        self.required_if(PENDING, field="cm_in_csf", field_required="cm_in_csf_date")
        self.applicable_if(YES, field="cm_in_csf", field_applicable="cm_in_csf_method")
        self.required_if(
            OTHER, field="cm_in_csf_method", field_required="cm_in_csf_method_other"
        )
        if (
            self.cleaned_data.get("cm_in_csf_date")
            and self.cleaned_data.get("lp_date")
            and (self.cleaned_data.get("lp_date") > self.cleaned_data.get("cm_in_csf_date"))
        ):
            raise forms.ValidationError(
                {"cm_in_csf_date": "Invalid. Cannot be before LP date"}
            )
        if (
            self.cleaned_data.get("cm_in_csf_date")
            and self.report_datetime
            and (
                to_local(self.report_datetime).date() > self.cleaned_data.get("cm_in_csf_date")
            )
        ):
            raise forms.ValidationError(
                {"cm_in_csf_date": "Invalid. Cannot be before report date"}
            )

    def validate_pregnancy(self) -> None:
        if (
            self.cleaned_data.get("gender") == MALE
            and self.cleaned_data.get("pregnant") != NOT_APPLICABLE
        ):
            raise forms.ValidationError({"pregnant": "Invalid. Subject is male"})
        if self.cleaned_data.get("gender") == MALE and self.cleaned_data.get("preg_test_date"):
            raise forms.ValidationError({"preg_test_date": "Invalid. Subject is male"})
        self.applicable_if(FEMALE, field="gender", field_applicable="breast_feeding")

    def validate_age(self) -> None:
        if self.age_in_years is not None and not (18 <= self.age_in_years < 120):
            raise forms.ValidationError(
                {"age_in_years": "Invalid. Subject must be 18 years or older"}
            )

    def validate_mg_ssx(self) -> None:
        self.validate_other_specify(
            field="any_other_mg_ssx",
            other_specify_field="any_other_mg_ssx_other",
            other_stored_value=YES,
        )

    def validate_suitability_for_study(self):
        self.required_if(
            YES, field="unsuitable_for_study", field_required="reasons_unsuitable"
        )
        self.applicable_if(
            YES, field="unsuitable_for_study", field_applicable="unsuitable_agreed"
        )
        if self.cleaned_data.get("unsuitable_agreed") == NO:
            raise forms.ValidationError(
                {
                    "unsuitable_agreed": "The study coordinator MUST agree "
                    "with your assessment. Please discuss before continuing."
                }
            )
