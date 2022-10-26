from edc_constants.constants import NO, NOT_APPLICABLE, NOT_DONE, YES
from edc_crf.crf_form_validator import CrfFormValidator
from edc_form_validators import INVALID_ERROR
from edc_visit_schedule.constants import WEEK10, WEEK24
from edc_visit_schedule.utils import is_baseline


class MentalStatusFormValidator(CrfFormValidator):

    reportable_fields = ["reportable_as_ae", "patient_admitted"]

    def clean(self) -> None:

        self.validate_if_baseline()

        self.validate_if_scheduled_w10_or_w24()

        self.validate_reporting_fieldset()

    def validate_if_baseline(self):
        """Validate criteria that only holds at baseline."""
        baseline = is_baseline(instance=self.related_visit)
        if baseline:
            for sx in ["recent_seizure", "behaviour_change", "confusion"]:
                if self.cleaned_data.get(sx) == YES:
                    self.raise_validation_error(
                        {sx: "Invalid. Cannot report positive symptoms at baseline."},
                        INVALID_ERROR,
                    )

            if self.cleaned_data.get("modified_rankin_score") not in ["0", NOT_DONE]:
                self.raise_validation_error(
                    {
                        "modified_rankin_score": (
                            "Invalid. Modified Rankin cannot be > 0 at baseline."
                        )
                    },
                    INVALID_ERROR,
                )
            elif self.cleaned_data.get("ecog_score") != "0":
                self.raise_validation_error(
                    {"ecog_score": "Invalid. ECOG cannot be > 0 at baseline."},
                    INVALID_ERROR,
                )
            elif (
                self.cleaned_data.get("glasgow_coma_score")
                and self.cleaned_data.get("glasgow_coma_score") < 15
            ):
                self.raise_validation_error(
                    {"glasgow_coma_score": "Invalid. GCS cannot be < 15 at baseline."},
                    INVALID_ERROR,
                )

    def validate_if_scheduled_w10_or_w24(self):
        """Validate criteria that only holds in w10 or w24 visits."""
        scheduled_w10_or_w24 = (
            self.related_visit.visit_code in [WEEK10, WEEK24]
            and self.related_visit.visit_code_sequence == 0
        )
        self.applicable_if_true(
            condition=scheduled_w10_or_w24,
            field_applicable="require_help",
            not_applicable_msg=(
                "This field is only applicable at scheduled Week 10 and Month 6 visits."
            ),
        )
        self.applicable_if_true(
            condition=scheduled_w10_or_w24,
            field_applicable="any_other_problems",
            not_applicable_msg=(
                "This field is only applicable at scheduled Week 10 and Month 6 visits."
            ),
        )

        if scheduled_w10_or_w24:
            require_help_response = self.cleaned_data.get("require_help")
            any_other_problems_response = self.cleaned_data.get("any_other_problems")
            modified_rankin_score_response = self.cleaned_data.get("modified_rankin_score")
            ecog_score_response = self.cleaned_data.get("ecog_score")
            error_msg = {}

            if require_help_response == YES or any_other_problems_response == YES:
                if modified_rankin_score_response == "0":
                    error_msg.update(
                        {
                            "modified_rankin_score": (
                                "Invalid. Expected to be > '0' or 'Not done' "
                                "if participant requires help or has any other problems."
                            ),
                        }
                    )
                if ecog_score_response == "0":
                    error_msg.update(
                        {
                            "ecog_score": (
                                "Invalid. Expected to be > '0' "
                                "if participant requires help or has any other problems."
                            ),
                        }
                    )

            elif require_help_response == NO and any_other_problems_response == NO:
                if modified_rankin_score_response not in ["0", NOT_DONE]:
                    error_msg.update(
                        {
                            "modified_rankin_score": (
                                "Invalid. Expected to be '0' or 'Not done' if participant "
                                "does not require help or have any other problems."
                            ),
                        }
                    )
                if ecog_score_response != "0":
                    error_msg.update(
                        {
                            "ecog_score": (
                                "Invalid. Expected to be '0' if participant "
                                "does not require help or have any other problems."
                            ),
                        }
                    )
            if error_msg:
                self.raise_validation_error(error_msg, INVALID_ERROR)

    def validate_reporting_fieldset(self):  # noqa: C901
        for fld in self.reportable_fields:
            if self.cleaned_data.get(fld) in [YES, NO]:
                # ae and hospitalization NOT reportable if no symptoms
                if (
                    self.cleaned_data.get("recent_seizure") == NO
                    and self.cleaned_data.get("behaviour_change") == NO
                    and self.cleaned_data.get("confusion") == NO
                    and self.cleaned_data.get("require_help") in [NOT_APPLICABLE, NO]
                    and self.cleaned_data.get("any_other_problems") in [NOT_APPLICABLE, NO]
                    and self.cleaned_data.get("modified_rankin_score") in ["0", NOT_DONE]
                    and self.cleaned_data.get("ecog_score") == "0"
                    and self.cleaned_data.get("glasgow_coma_score") == 15
                ):
                    self.raise_not_applicable(field=fld, msg="No symptoms were reported.")

            elif self.cleaned_data.get(fld) == NOT_APPLICABLE:
                # ae and hospitalization ARE reportable if any symptoms
                if self.cleaned_data.get("recent_seizure") == YES:
                    self.raise_applicable(field=fld, msg="A recent seizure was reported.")
                elif self.cleaned_data.get("behaviour_change") == YES:
                    self.raise_applicable(field=fld, msg="Behaviour change was reported.")
                elif self.cleaned_data.get("confusion") == YES:
                    self.raise_applicable(field=fld, msg="Confusion reported.")
                elif self.cleaned_data.get("require_help") == YES:
                    self.raise_applicable(
                        field=fld, msg="Reported help required for activities."
                    )
                elif self.cleaned_data.get("any_other_problems") == YES:
                    self.raise_applicable(field=fld, msg="Other problems reported.")
                elif self.cleaned_data.get("modified_rankin_score") not in ["0", NOT_DONE]:
                    self.raise_applicable(field=fld, msg="Modified Rankin Score > 0.")
                elif self.cleaned_data.get("ecog_score") != "0":
                    self.raise_applicable(field=fld, msg="ECOG score > 0.")
                elif (
                    self.cleaned_data.get("glasgow_coma_score")
                    and self.cleaned_data.get("glasgow_coma_score") < 15
                ):
                    self.raise_applicable(field=fld, msg="GCS < 15.")
