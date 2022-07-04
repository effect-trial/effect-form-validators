from edc_constants.constants import NO, NOT_APPLICABLE, NOT_DONE, YES
from edc_crf.crf_form_validator import CrfFormValidator
from edc_form_validators import INVALID_ERROR
from edc_visit_schedule.utils import is_baseline


class MentalStatusFormValidator(CrfFormValidator):

    reportable_fields = ["reportable_as_ae", "patient_admitted"]

    def clean(self) -> None:

        baseline = is_baseline(instance=self.cleaned_data.get("subject_visit"))

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

        self.validate_reporting_fieldset()

    def validate_reporting_fieldset(self):  # noqa: C901
        for fld in self.reportable_fields:
            if self.cleaned_data.get(fld) in [YES, NO]:
                # ae and hospitalization NOT reportable if no symptoms
                if (
                    self.cleaned_data.get("recent_seizure") == NO
                    and self.cleaned_data.get("behaviour_change") == NO
                    and self.cleaned_data.get("confusion") == NO
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
                elif self.cleaned_data.get("modified_rankin_score") not in ["0", NOT_DONE]:
                    self.raise_applicable(field=fld, msg="Modified Rankin Score > 0.")
                elif self.cleaned_data.get("ecog_score") != "0":
                    self.raise_applicable(field=fld, msg="ECOG score > 0.")
                elif (
                    self.cleaned_data.get("glasgow_coma_score")
                    and self.cleaned_data.get("glasgow_coma_score") < 15
                ):
                    self.raise_applicable(field=fld, msg="GCS < 15.")
