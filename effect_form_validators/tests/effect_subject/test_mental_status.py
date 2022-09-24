from typing import Optional
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django_mock_queries.query import MockModel
from edc_constants.constants import NO, NOT_APPLICABLE, NOT_DONE, YES
from edc_visit_schedule.constants import DAY01, DAY14, WEEK10, WEEK24

from effect_form_validators.effect_subject import MentalStatusFormValidator as Base

from ..mixins import FormValidatorTestMixin, TestCaseMixin


class MentalStatusMockModel(MockModel):
    @classmethod
    def related_visit_model_attr(cls):
        return "subject_visit"


class MentalStatusFormValidator(FormValidatorTestMixin, Base):
    pass


class TestMentalStatusFormValidation(TestCaseMixin, TestCase):
    reportable_fields = ["reportable_as_ae", "patient_admitted"]

    def setUp(self) -> None:
        super().setUp()
        patcher = patch(
            "effect_form_validators.effect_subject.mental_status_form_validator.is_baseline"
        )
        self.addCleanup(patcher.stop)
        self.mock_is_baseline = patcher.start()

    def get_cleaned_data(
        self,
        visit_code: Optional[str] = None,
        visit_code_sequence: Optional[int] = None,
        **kwargs,
    ) -> dict:
        cleaned_data = super().get_cleaned_data(
            visit_code=visit_code,
            visit_code_sequence=visit_code_sequence,
            **kwargs,
        )
        scheduled_w10_or_w24 = (
            cleaned_data.get("subject_visit").visit_code in [WEEK10, WEEK24]
            and cleaned_data.get("subject_visit").visit_code_sequence == 0
        )
        cleaned_data.update(
            {
                "recent_seizure": NO,
                "behaviour_change": NO,
                "confusion": NO,
                "require_help": NO if scheduled_w10_or_w24 else NOT_APPLICABLE,
                "any_other_problems": NO if scheduled_w10_or_w24 else NOT_APPLICABLE,
                "modified_rankin_score": "0",
                "ecog_score": "0",
                "glasgow_coma_score": 15,
                "reportable_as_ae": NOT_APPLICABLE,
                "patient_admitted": NOT_APPLICABLE,
            }
        )
        return cleaned_data

    def test_cleaned_data_at_baseline_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        form_validator = MentalStatusFormValidator(
            cleaned_data=cleaned_data, model=MentalStatusMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_cleaned_data_at_subsequent_visits_ok(self):
        self.mock_is_baseline.return_value = False
        for visit_code in self.visit_schedule:
            with self.subTest(visit_code=visit_code):
                cleaned_data = self.get_cleaned_data(
                    visit_code=visit_code,
                    visit_code_sequence=1 if visit_code == DAY01 else 0,
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reportable_fieldset_not_applicable_at_baseline(self):
        self.mock_is_baseline.return_value = True
        for reporting_field in self.reportable_fields:
            for response in [YES, NO]:
                with self.subTest(reporting_field=reporting_field, response=response):
                    cleaned_data = self.get_cleaned_data(visit_code=DAY01)
                    cleaned_data.update({reporting_field: response})
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn(reporting_field, cm.exception.error_dict)
                    self.assertIn(
                        "This field is not applicable. No symptoms were reported.",
                        str(cm.exception.error_dict.get(reporting_field)),
                    )

    def test_reporting_fieldset_can_be_not_applicable_after_baseline(self):
        self.mock_is_baseline.return_value = False
        for visit_code in self.visit_schedule:
            with self.subTest(visit_code=visit_code):
                cleaned_data = self.get_cleaned_data(
                    visit_code=visit_code,
                    visit_code_sequence=1 if visit_code == DAY01 else 0,
                )
                cleaned_data.update(
                    {
                        "recent_seizure": NO,
                        "behaviour_change": NO,
                        "confusion": NO,
                        "modified_rankin_score": "0",
                        "ecog_score": "0",
                        "glasgow_coma_score": 15,
                        "reportable_as_ae": NOT_APPLICABLE,
                        "patient_admitted": NOT_APPLICABLE,
                    }
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reporting_fieldset_can_be_answered_after_baseline(self):
        self.mock_is_baseline.return_value = False
        for visit_code in self.visit_schedule:
            with self.subTest(visit_code=visit_code):
                cleaned_data = self.get_cleaned_data(
                    visit_code=visit_code,
                    visit_code_sequence=1 if visit_code == DAY01 else 0,
                )
                cleaned_data.update(
                    {
                        "recent_seizure": NO,
                        "behaviour_change": NO,
                        "confusion": YES,  # <-- any sx makes reporting fieldset applicable
                        "modified_rankin_score": "0",
                        "ecog_score": "0",
                        "glasgow_coma_score": 15,
                        "reportable_as_ae": NO,
                        "patient_admitted": YES,
                    }
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_positive_yn_sx_at_baseline_raises_error(self):
        self.mock_is_baseline.return_value = True
        for sx in ["recent_seizure", "behaviour_change", "confusion"]:
            with self.subTest(sx=sx):
                cleaned_data = self.get_cleaned_data(visit_code=DAY01)
                cleaned_data.update({sx: YES})
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn(sx, cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Cannot report positive symptoms at baseline.",
                    str(cm.exception.error_dict.get(sx)),
                )

    def test_modified_rankin_score_gt_0_at_baseline_raises_error(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        for modified_rankin_score in [1, 6]:
            with self.subTest(modified_rankin_score=modified_rankin_score):
                cleaned_data.update({"modified_rankin_score": modified_rankin_score})
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("modified_rankin_score", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Modified Rankin cannot be > 0 at baseline.",
                    str(cm.exception.error_dict.get("modified_rankin_score")),
                )

    def test_ecog_score_gt_0_at_baseline_raises_error(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        for ecog_score in [1, 5]:
            with self.subTest(ecog_score=ecog_score):
                cleaned_data.update({"ecog_score": ecog_score})
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("ecog_score", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. ECOG cannot be > 0 at baseline.",
                    str(cm.exception.error_dict.get("ecog_score")),
                )

    def test_gcs_lt_15_at_baseline_raises_error(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        for gcs in [3, 14]:
            with self.subTest(gcs=gcs):
                cleaned_data.update({"glasgow_coma_score": gcs})
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("glasgow_coma_score", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. GCS cannot be < 15 at baseline.",
                    str(cm.exception.error_dict.get("glasgow_coma_score")),
                )

    def test_negative_yn_sx_at_baseline_ok(self):
        self.mock_is_baseline.return_value = True
        for sx in ["recent_seizure", "behaviour_change", "confusion"]:
            with self.subTest(sx=sx):
                cleaned_data = self.get_cleaned_data(visit_code=DAY01)
                cleaned_data.update(
                    {
                        sx: NO,
                        "reportable_as_ae": NOT_APPLICABLE,
                        "patient_admitted": NOT_APPLICABLE,
                    }
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_modified_rankin_score_0_at_baseline_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        cleaned_data.update(
            {
                "modified_rankin_score": "0",
                "reportable_as_ae": NOT_APPLICABLE,
                "patient_admitted": NOT_APPLICABLE,
            }
        )
        form_validator = MentalStatusFormValidator(
            cleaned_data=cleaned_data, model=MentalStatusMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_modified_rankin_score_not_done_at_baseline_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        cleaned_data.update(
            {
                "modified_rankin_score": NOT_DONE,
                "reportable_as_ae": NOT_APPLICABLE,
                "patient_admitted": NOT_APPLICABLE,
            }
        )
        form_validator = MentalStatusFormValidator(
            cleaned_data=cleaned_data, model=MentalStatusMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_ecog_score_0_at_baseline_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        cleaned_data.update(
            {
                "ecog_score": "0",
                "reportable_as_ae": NOT_APPLICABLE,
                "patient_admitted": NOT_APPLICABLE,
            }
        )
        form_validator = MentalStatusFormValidator(
            cleaned_data=cleaned_data, model=MentalStatusMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_gcs_15_at_baseline_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        cleaned_data.update(
            {
                "gcs": 15,
                "reportable_as_ae": NOT_APPLICABLE,
                "patient_admitted": NOT_APPLICABLE,
            }
        )
        form_validator = MentalStatusFormValidator(
            cleaned_data=cleaned_data, model=MentalStatusMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_positive_yn_sx_after_baseline_ok(self):
        self.mock_is_baseline.return_value = False
        for sx in ["recent_seizure", "behaviour_change", "confusion"]:
            for visit_code in self.visit_schedule:
                with self.subTest(sx=sx, visit_code=visit_code):
                    cleaned_data = self.get_cleaned_data(
                        visit_code=visit_code,
                        visit_code_sequence=1 if visit_code == DAY01 else 0,
                    )
                    cleaned_data.update(
                        {
                            sx: YES,
                            "reportable_as_ae": NO,
                            "patient_admitted": NO,
                        }
                    )
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_modified_rankin_score_gt_0_after_baseline_ok(self):
        self.mock_is_baseline.return_value = False
        for visit_code in self.visit_schedule:
            for modified_rankin_score in [1, 6]:
                with self.subTest(
                    visit_code=visit_code, modified_rankin_score=modified_rankin_score
                ):
                    cleaned_data = self.get_cleaned_data(
                        visit_code=visit_code,
                        visit_code_sequence=1 if visit_code == DAY01 else 0,
                    )
                    cleaned_data.update(
                        {
                            "modified_rankin_score": modified_rankin_score,
                            "reportable_as_ae": NO,
                            "patient_admitted": NO,
                        }
                    )
                    if visit_code in [WEEK10, WEEK24]:
                        # appease w10/w24 validation
                        cleaned_data.update(
                            {
                                "require_help": YES,
                                "ecog_score": "1",
                            }
                        )
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_ecog_score_gt_0_after_baseline_ok(self):
        self.mock_is_baseline.return_value = False
        for visit_code in self.visit_schedule:
            for ecog_score in [1, 5]:
                with self.subTest(visit_code=visit_code, ecog_score=ecog_score):
                    cleaned_data = self.get_cleaned_data(
                        visit_code=visit_code,
                        visit_code_sequence=1 if visit_code == DAY01 else 0,
                    )
                    cleaned_data.update(
                        {
                            "ecog_score": ecog_score,
                            "reportable_as_ae": NO,
                            "patient_admitted": NO,
                        }
                    )
                    if visit_code in [WEEK10, WEEK24]:
                        # appease w10/w24 validation
                        cleaned_data.update(
                            {
                                "require_help": YES,
                                "modified_rankin_score": "1",
                            }
                        )

                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_gcs_lt_15_after_baseline_ok(self):
        self.mock_is_baseline.return_value = False
        for visit_code in self.visit_schedule:
            for gcs in [3, 14]:
                with self.subTest(visit_code=visit_code, gcs=gcs):
                    cleaned_data = self.get_cleaned_data(
                        visit_code=visit_code,
                        visit_code_sequence=1 if visit_code == DAY01 else 0,
                    )
                    cleaned_data.update(
                        {
                            "glasgow_coma_score": gcs,
                            "reportable_as_ae": NO,
                            "patient_admitted": NO,
                        }
                    )
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_require_help_applicable_at_scheduled_w10_and_w24_visits(self):
        self.mock_is_baseline.return_value = False
        for visit_code in [WEEK10, WEEK24]:
            with self.subTest(visit_code=visit_code):
                cleaned_data = self.get_cleaned_data(
                    visit_code=visit_code,
                    visit_code_sequence=0,
                )
                cleaned_data.update({"require_help": NOT_APPLICABLE})
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("require_help", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("require_help")),
                )

                cleaned_data.update(
                    {
                        "require_help": YES,
                        # appease w10/w24 validation
                        "modified_rankin_score": "1",
                        "ecog_score": "1",
                        "reportable_as_ae": NO,
                        "patient_admitted": NO,
                    }
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_require_help_not_applicable_at_unscheduled_w10_and_w24_visits(self):
        self.mock_is_baseline.return_value = False
        for visit_code in [WEEK10, WEEK24]:
            for visit_code_sequence in [1, 2, 3]:
                with self.subTest(
                    visit_code=visit_code,
                    visit_code_sequence=visit_code_sequence,
                ):
                    cleaned_data = self.get_cleaned_data(
                        visit_code=visit_code,
                        visit_code_sequence=visit_code_sequence,
                    )
                    cleaned_data.update({"require_help": NO})
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn("require_help", cm.exception.error_dict)
                    self.assertIn(
                        "This field is only applicable at scheduled "
                        "Week 10 and Month 6 visits.",
                        str(cm.exception.error_dict.get("require_help")),
                    )

                    cleaned_data.update({"require_help": NOT_APPLICABLE})
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_require_help_not_applicable_if_not_w10_and_w24(self):
        for visit_code in [vc for vc in self.visit_schedule if vc not in [WEEK10, WEEK24]]:
            for visit_code_sequence in [0, 1]:
                with self.subTest(
                    visit_code=visit_code,
                    visit_code_sequence=visit_code_sequence,
                ):
                    self.mock_is_baseline.return_value = (
                        visit_code == DAY01 and visit_code_sequence == 0
                    )
                    cleaned_data = self.get_cleaned_data(
                        visit_code=visit_code,
                        visit_code_sequence=visit_code_sequence,
                    )
                    cleaned_data.update({"require_help": YES})
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn("require_help", cm.exception.error_dict)
                    self.assertIn(
                        "This field is only applicable at scheduled "
                        "Week 10 and Month 6 visits.",
                        str(cm.exception.error_dict.get("require_help")),
                    )

                    cleaned_data.update({"require_help": NOT_APPLICABLE})
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_any_other_problems_applicable_at_scheduled_w10_and_w24_visits(self):
        self.mock_is_baseline.return_value = False
        for visit_code in [WEEK10, WEEK24]:
            with self.subTest(visit_code=visit_code):
                cleaned_data = self.get_cleaned_data(
                    visit_code=visit_code,
                    visit_code_sequence=0,
                )
                cleaned_data.update({"any_other_problems": NOT_APPLICABLE})
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("any_other_problems", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("any_other_problems")),
                )

                cleaned_data.update(
                    {
                        "any_other_problems": YES,
                        # appease w10/w24 validation
                        "modified_rankin_score": "1",
                        "ecog_score": "1",
                        "reportable_as_ae": NO,
                        "patient_admitted": NO,
                    }
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_any_other_problems_not_applicable_at_unscheduled_w10_and_w24_visits(self):
        self.mock_is_baseline.return_value = False
        for visit_code in [WEEK10, WEEK24]:
            for visit_code_sequence in [1, 2, 3]:
                with self.subTest(
                    visit_code=visit_code,
                    visit_code_sequence=visit_code_sequence,
                ):
                    cleaned_data = self.get_cleaned_data(
                        visit_code=visit_code,
                        visit_code_sequence=visit_code_sequence,
                    )
                    cleaned_data.update({"any_other_problems": NO})
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn("any_other_problems", cm.exception.error_dict)
                    self.assertIn(
                        "This field is only applicable at scheduled "
                        "Week 10 and Month 6 visits.",
                        str(cm.exception.error_dict.get("any_other_problems")),
                    )

                    cleaned_data.update({"any_other_problems": NOT_APPLICABLE})
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_any_other_problems_not_applicable_if_not_w10_and_w24(self):
        for visit_code in [vc for vc in self.visit_schedule if vc not in [WEEK10, WEEK24]]:
            for visit_code_sequence in [0, 1]:
                with self.subTest(
                    visit_code=visit_code,
                    visit_code_sequence=visit_code_sequence,
                ):
                    self.mock_is_baseline.return_value = (
                        visit_code == DAY01 and visit_code_sequence == 0
                    )
                    cleaned_data = self.get_cleaned_data(
                        visit_code=visit_code,
                        visit_code_sequence=visit_code_sequence,
                    )
                    cleaned_data.update({"any_other_problems": YES})
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn("any_other_problems", cm.exception.error_dict)
                    self.assertIn(
                        "This field is only applicable at scheduled "
                        "Week 10 and Month 6 visits.",
                        str(cm.exception.error_dict.get("any_other_problems")),
                    )

                    cleaned_data.update({"any_other_problems": NOT_APPLICABLE})
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_raises_if_positive_w10_or_w24_answer_and_ecog_or_modified_rankin_0(
        self,
    ):
        self.mock_is_baseline.return_value = False
        for requires_help_response, any_other_problems_response in [
            (YES, NO),
            (NO, YES),
            (YES, YES),
        ]:
            with self.subTest(
                require_help=requires_help_response,
                any_other_problems=any_other_problems_response,
            ):
                # Test both ECOG and Modified Rankin 0
                cleaned_data = self.get_cleaned_data(visit_code=WEEK10)
                cleaned_data.update(
                    {
                        "require_help": requires_help_response,
                        "any_other_problems": any_other_problems_response,
                        "modified_rankin_score": "0",
                        "ecog_score": "0",
                        "reportable_as_ae": NO,
                        "patient_admitted": NO,
                    }
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("modified_rankin_score", cm.exception.error_dict)
                expected_modified_rankin_error_message = (
                    "Invalid. "
                    "Expected to be > '0' or 'Not done' "
                    "if participant requires help or has any other problems."
                )
                self.assertIn(
                    expected_modified_rankin_error_message,
                    str(cm.exception.error_dict.get("modified_rankin_score")),
                )

                self.assertIn("ecog_score", cm.exception.error_dict)
                expected_ecog_error_message = (
                    "Invalid. "
                    "Expected to be > '0' "
                    "if participant requires help or has any other problems."
                )
                self.assertIn(
                    expected_ecog_error_message,
                    str(cm.exception.error_dict.get("ecog_score")),
                )

                # Test only ECOG 0
                cleaned_data.update(
                    {
                        "modified_rankin_score": "1",
                        "ecog_score": "0",
                    }
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("ecog_score", cm.exception.error_dict)
                self.assertIn(
                    expected_ecog_error_message,
                    str(cm.exception.error_dict.get("ecog_score")),
                )

                # Test only Modified Rankin 0
                cleaned_data.update(
                    {
                        "modified_rankin_score": "0",
                        "ecog_score": "1",
                    }
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("modified_rankin_score", cm.exception.error_dict)
                self.assertIn(
                    expected_modified_rankin_error_message,
                    str(cm.exception.error_dict.get("modified_rankin_score")),
                )

                # Test ECOG 0 and Modified Rankin not done
                cleaned_data.update(
                    {
                        "modified_rankin_score": NOT_DONE,
                        "ecog_score": "0",
                    }
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("ecog_score", cm.exception.error_dict)
                self.assertIn(
                    expected_ecog_error_message,
                    str(cm.exception.error_dict.get("ecog_score")),
                )

    def test_ok_if_positive_w10_or_w24_answer_and_neither_ecog_or_modified_rankin_score_0(
        self,
    ):
        self.mock_is_baseline.return_value = False
        for requires_help_response, any_other_problems_response in [
            (YES, NO),
            (NO, YES),
            (YES, YES),
        ]:
            for mrs_score, ecog_score in [
                ("1", "1"),
                ("2", "3"),
                ("6", "5"),
                (NOT_DONE, "1"),
            ]:
                with self.subTest(
                    require_help=requires_help_response,
                    any_other_problems=any_other_problems_response,
                    mrs_score=mrs_score,
                    ecog_score=ecog_score,
                ):
                    cleaned_data = self.get_cleaned_data(visit_code=WEEK10)
                    cleaned_data.update(
                        {
                            "require_help": requires_help_response,
                            "any_other_problems": any_other_problems_response,
                            "modified_rankin_score": mrs_score,
                            "ecog_score": ecog_score,
                            "reportable_as_ae": NO,
                            "patient_admitted": NO,
                        }
                    )

                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_raises_if_both_w10_or_w24_answers_negative_and_ecog_or_modified_rankin_not_0(
        self,
    ):
        self.mock_is_baseline.return_value = False
        # Test neither ECOG nor Modified Rankin 0
        cleaned_data = self.get_cleaned_data(visit_code=WEEK10)
        cleaned_data.update(
            {
                "require_help": NO,
                "any_other_problems": NO,
                "modified_rankin_score": "1",
                "ecog_score": "2",
                "reportable_as_ae": NO,
                "patient_admitted": NO,
            }
        )
        form_validator = MentalStatusFormValidator(
            cleaned_data=cleaned_data, model=MentalStatusMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("modified_rankin_score", cm.exception.error_dict)
        expected_modified_rankin_error_message = (
            "Invalid. "
            "Expected to be '0' or 'Not done' "
            "if participant does not require help or have any other problems."
        )
        self.assertIn(
            expected_modified_rankin_error_message,
            str(cm.exception.error_dict.get("modified_rankin_score")),
        )

        self.assertIn("ecog_score", cm.exception.error_dict)
        expected_ecog_error_message = (
            "Invalid. "
            "Expected to be '0' "
            "if participant does not require help or have any other problems."
        )
        self.assertIn(
            expected_ecog_error_message,
            str(cm.exception.error_dict.get("ecog_score")),
        )

        # Test Modified Rankin not 0
        cleaned_data.update(
            {
                "modified_rankin_score": "1",
                "ecog_score": "0",
            }
        )
        form_validator = MentalStatusFormValidator(
            cleaned_data=cleaned_data, model=MentalStatusMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("modified_rankin_score", cm.exception.error_dict)
        self.assertIn(
            expected_modified_rankin_error_message,
            str(cm.exception.error_dict.get("modified_rankin_score")),
        )

        # Test ECOG not 0
        cleaned_data.update(
            {
                "modified_rankin_score": "0",
                "ecog_score": "1",
            }
        )
        form_validator = MentalStatusFormValidator(
            cleaned_data=cleaned_data, model=MentalStatusMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("ecog_score", cm.exception.error_dict)
        self.assertIn(
            expected_ecog_error_message,
            str(cm.exception.error_dict.get("ecog_score")),
        )

        # Test ECOG not 0 and Modified Rankin not done
        cleaned_data.update(
            {
                "modified_rankin_score": NOT_DONE,
                "ecog_score": "1",
            }
        )
        form_validator = MentalStatusFormValidator(
            cleaned_data=cleaned_data, model=MentalStatusMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("ecog_score", cm.exception.error_dict)
        self.assertIn(
            expected_ecog_error_message,
            str(cm.exception.error_dict.get("ecog_score")),
        )

    def test_ok_if_both_w10_or_w24_answers_negative_and_ecog_and_modified_rankin_score_0(
        self,
    ):
        self.mock_is_baseline.return_value = False
        for modified_rankin_response in ["0", NOT_DONE]:
            with self.subTest(modified_rankin_response=modified_rankin_response):
                cleaned_data = self.get_cleaned_data(visit_code=WEEK10)
                cleaned_data.update(
                    {
                        "require_help": NO,
                        "any_other_problems": NO,
                        "modified_rankin_score": modified_rankin_response,
                        "ecog_score": "0",
                        "reportable_as_ae": NOT_APPLICABLE,
                        "patient_admitted": NOT_APPLICABLE,
                    }
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reporting_fieldset_applicable_if_symptom_reported(self):
        self.mock_is_baseline.return_value = False
        for symptom_fld in ["recent_seizure", "behaviour_change", "confusion"]:
            with self.subTest(condition_fld=symptom_fld):
                cleaned_data = self.get_cleaned_data(visit_code=DAY14)
                cleaned_data.update(
                    {
                        symptom_fld: YES,
                        "reportable_as_ae": NOT_APPLICABLE,
                        "patient_admitted": NOT_APPLICABLE,
                    }
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("reportable_as_ae", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("reportable_as_ae")),
                )

                cleaned_data.update({"reportable_as_ae": NO})
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("patient_admitted", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("patient_admitted")),
                )

                cleaned_data.update({"patient_admitted": NO})
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reporting_fieldset_applicable_if_w10_or_w24_symptom_reported(self):
        self.mock_is_baseline.return_value = False
        for visit_code in [WEEK10, WEEK24]:
            for symptom_fld in ["require_help", "any_other_problems"]:
                with self.subTest(visit_code, symptom_fld=symptom_fld):
                    cleaned_data = self.get_cleaned_data(visit_code=visit_code)
                    cleaned_data.update(
                        {
                            symptom_fld: YES,
                            # appease w10/w24 validation
                            "modified_rankin_score": "1",
                            "ecog_score": "1",
                            "reportable_as_ae": NOT_APPLICABLE,
                            "patient_admitted": NOT_APPLICABLE,
                        }
                    )
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn("reportable_as_ae", cm.exception.error_dict)
                    self.assertIn(
                        "This field is applicable.",
                        str(cm.exception.error_dict.get("reportable_as_ae")),
                    )

                    cleaned_data.update({"reportable_as_ae": NO})
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn("patient_admitted", cm.exception.error_dict)
                    self.assertIn(
                        "This field is applicable.",
                        str(cm.exception.error_dict.get("patient_admitted")),
                    )

                    cleaned_data.update({"patient_admitted": NO})
                    form_validator = MentalStatusFormValidator(
                        cleaned_data=cleaned_data, model=MentalStatusMockModel
                    )
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reporting_fieldset_applicable_if_modified_rankin_score_1_to_5(self):
        self.mock_is_baseline.return_value = False
        for score in ["1", "2", "3", "4", "5", "6"]:
            with self.subTest(modified_rankin_score=score):
                cleaned_data = self.get_cleaned_data(visit_code=DAY14)
                cleaned_data.update(
                    {
                        "modified_rankin_score": score,
                        "reportable_as_ae": NOT_APPLICABLE,
                        "patient_admitted": NOT_APPLICABLE,
                    }
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("reportable_as_ae", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("reportable_as_ae")),
                )

                cleaned_data.update({"reportable_as_ae": NO})
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("patient_admitted", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("patient_admitted")),
                )

                cleaned_data.update({"patient_admitted": NO})
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reporting_fieldset_applicable_if_ecog_1_to_5(self):
        self.mock_is_baseline.return_value = False
        for score in ["1", "2", "3", "4", "5"]:
            with self.subTest(ecog_score=score):
                cleaned_data = self.get_cleaned_data(visit_code=DAY14)
                cleaned_data.update(
                    {
                        "ecog_score": score,
                        "reportable_as_ae": NOT_APPLICABLE,
                        "patient_admitted": NOT_APPLICABLE,
                    }
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("reportable_as_ae", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("reportable_as_ae")),
                )

                cleaned_data.update({"reportable_as_ae": NO})
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("patient_admitted", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("patient_admitted")),
                )

                cleaned_data.update({"patient_admitted": NO})
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reporting_fieldset_applicable_if_gcs_lt_15(self):
        self.mock_is_baseline.return_value = False
        for score in range(3, 14):
            with self.subTest(gcs=score):
                cleaned_data = self.get_cleaned_data(visit_code=DAY14)
                cleaned_data.update(
                    {
                        "glasgow_coma_score": score,
                        "reportable_as_ae": NOT_APPLICABLE,
                        "patient_admitted": NOT_APPLICABLE,
                    }
                )
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("reportable_as_ae", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("reportable_as_ae")),
                )

                cleaned_data.update({"reportable_as_ae": NO})
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("patient_admitted", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("patient_admitted")),
                )

                cleaned_data.update({"patient_admitted": NO})
                form_validator = MentalStatusFormValidator(
                    cleaned_data=cleaned_data, model=MentalStatusMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_gcs_blank_with_reporting_fieldset_not_applicable_does_not_raise(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY14)
        cleaned_data.update(
            {
                "glasgow_coma_score": None,
                "reportable_as_ae": NOT_APPLICABLE,
                "patient_admitted": NOT_APPLICABLE,
            }
        )
        form_validator = MentalStatusFormValidator(
            cleaned_data=cleaned_data, model=MentalStatusMockModel
        )
        try:
            form_validator.validate()
        except TypeError as e:
            self.fail(f"TypeError unexpectedly raised.  Got {e}")
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_gcs_blank_with_reporting_fieldset_applicable_does_not_raise(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY14)
        cleaned_data.update(
            {
                "glasgow_coma_score": None,
                "reportable_as_ae": NO,
                "patient_admitted": NO,
            }
        )
        form_validator = MentalStatusFormValidator(
            cleaned_data=cleaned_data, model=MentalStatusMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reporting_fieldset_not_applicable_if_no_symptoms_reported(self):
        self.mock_is_baseline.return_value = False
        for reporting_fld in self.reportable_fields:
            for reporting_fld_answer in [YES, NO]:
                for mrs_response in ["0", NOT_DONE]:
                    with self.subTest(
                        reporting_fld=reporting_fld,
                        reporting_fld_answer=reporting_fld_answer,
                        mrs_response=mrs_response,
                    ):
                        cleaned_data = self.get_cleaned_data(visit_code=DAY14)
                        cleaned_data.update(
                            {
                                "recent_seizure": NO,
                                "behaviour_change": NO,
                                "confusion": NO,
                                "require_help": NOT_APPLICABLE,
                                "any_other_problems": NOT_APPLICABLE,
                                "modified_rankin_score": mrs_response,
                                "ecog_score": "0",
                                "glasgow_coma_score": 15,
                                "reportable_as_ae": NOT_APPLICABLE,
                                "patient_admitted": NOT_APPLICABLE,
                            }
                        )

                        form_validator = MentalStatusFormValidator(
                            cleaned_data=cleaned_data, model=MentalStatusMockModel
                        )
                        try:
                            form_validator.validate()
                        except ValidationError as e:
                            self.fail(f"ValidationError unexpectedly raised. Got {e}")

                        cleaned_data.update({reporting_fld: reporting_fld_answer})
                        form_validator = MentalStatusFormValidator(
                            cleaned_data=cleaned_data, model=MentalStatusMockModel
                        )
                        with self.assertRaises(ValidationError) as cm:
                            form_validator.validate()
                        self.assertIn(reporting_fld, cm.exception.error_dict)
                        self.assertIn(
                            "This field is not applicable. No symptoms were reported.",
                            str(cm.exception.error_dict.get(reporting_fld)),
                        )

    def test_reporting_fieldset_not_applicable_if_no_w10_or_w24_symptoms_reported(self):
        self.mock_is_baseline.return_value = False
        for visit_code in [WEEK10, WEEK24]:
            for reporting_fld in self.reportable_fields:
                for reporting_fld_answer in [YES, NO]:
                    with self.subTest(
                        visit_code=visit_code,
                        reporting_fld=reporting_fld,
                        reporting_fld_answer=reporting_fld_answer,
                    ):
                        cleaned_data = self.get_cleaned_data(visit_code=visit_code)
                        cleaned_data.update(
                            {
                                "require_help": NO,
                                "any_other_problems": NO,
                                "reportable_as_ae": NOT_APPLICABLE,
                                "patient_admitted": NOT_APPLICABLE,
                            }
                        )

                        form_validator = MentalStatusFormValidator(
                            cleaned_data=cleaned_data, model=MentalStatusMockModel
                        )
                        try:
                            form_validator.validate()
                        except ValidationError as e:
                            self.fail(f"ValidationError unexpectedly raised. Got {e}")

                        cleaned_data.update({reporting_fld: reporting_fld_answer})
                        form_validator = MentalStatusFormValidator(
                            cleaned_data=cleaned_data, model=MentalStatusMockModel
                        )
                        with self.assertRaises(ValidationError) as cm:
                            form_validator.validate()
                        self.assertIn(reporting_fld, cm.exception.error_dict)
                        self.assertIn(
                            "This field is not applicable. No symptoms were reported.",
                            str(cm.exception.error_dict.get(reporting_fld)),
                        )
