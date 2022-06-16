from typing import Optional
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from edc_constants.constants import NO, NOT_APPLICABLE, YES
from effect_visit_schedule.constants import DAY01, DAY14

from effect_form_validators.effect_subject import MentalStatusFormValidator as Base

from ..mixins import FormValidatorTestMixin, TestCaseMixin


class MentalStatusFormValidator(FormValidatorTestMixin, Base):
    pass


class TestMentalStatusFormValidation(TestCaseMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        patcher = patch(
            "effect_form_validators.effect_subject.mental_status_form_validator.is_baseline"
        )
        self.addCleanup(patcher.stop)
        self.mock_is_baseline = patcher.start()

    def get_cleaned_data(self, visit_code: Optional[str] = None, **kwargs) -> dict:
        cleaned_data = super().get_cleaned_data(visit_code=visit_code, **kwargs)
        cleaned_data.update(
            {
                "recent_seizure": NO,
                "behaviour_change": NO,
                "confusion": NO,
                "modified_rankin_score": "0",
                "ecog_score": "0",
                "glasgow_coma_score": 15,
                "reportable_as_ae": NOT_APPLICABLE if visit_code == DAY01 else NO,
                "patient_admitted": NOT_APPLICABLE if visit_code == DAY01 else NO,
            }
        )

        return cleaned_data

    def test_cleaned_data_at_baseline_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        form_validator = MentalStatusFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_cleaned_data_at_d14_ok(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY14)
        form_validator = MentalStatusFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reportable_as_ae_not_applicable_at_baseline(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        for response in [YES, NO]:
            with self.subTest(reportable_as_ae=response):
                cleaned_data.update({"reportable_as_ae": response})
                form_validator = MentalStatusFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("reportable_as_ae", cm.exception.error_dict)
                self.assertIn(
                    "Not applicable at baseline",
                    str(cm.exception.error_dict.get("reportable_as_ae")),
                )

    def test_patient_admitted_not_applicable_at_baseline(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        for response in [YES, NO]:
            with self.subTest(patient_admitted=response):
                cleaned_data.update({"patient_admitted": response})
                form_validator = MentalStatusFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("patient_admitted", cm.exception.error_dict)
                self.assertIn(
                    "Not applicable at baseline.",
                    str(cm.exception.error_dict.get("patient_admitted")),
                )

    def test_reportable_as_ae_applicable_at_d14(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY14)
        cleaned_data.update({"reportable_as_ae": NOT_APPLICABLE})
        form_validator = MentalStatusFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("reportable_as_ae", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("reportable_as_ae")),
        )
        for response in [YES, NO]:
            with self.subTest(reportable_as_ae=response):
                cleaned_data.update({"reportable_as_ae": response})
                form_validator = MentalStatusFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_patient_admitted_applicable_at_d14(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY14)
        cleaned_data.update({"patient_admitted": NOT_APPLICABLE})
        form_validator = MentalStatusFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("patient_admitted", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("patient_admitted")),
        )
        for response in [YES, NO]:
            with self.subTest(patient_admitted=response):
                cleaned_data.update({"patient_admitted": response})
                form_validator = MentalStatusFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_seizures_at_baseline_raises_error(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        cleaned_data.update({"recent_seizure": YES})
        form_validator = MentalStatusFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("recent_seizure", cm.exception.error_dict)
        self.assertIn(
            "Invalid. Cannot have had a recent seizure at baseline",
            str(cm.exception.error_dict.get("recent_seizure")),
        )

    def test_gcs_lt_15_at_baseline_raises_error(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        for gcs in [3, 14]:
            with self.subTest(gcs=gcs):
                cleaned_data.update({"glasgow_coma_score": gcs})
                form_validator = MentalStatusFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("glasgow_coma_score", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. GCS cannot be less than 15 at baseline",
                    str(cm.exception.error_dict.get("glasgow_coma_score")),
                )

    def test_seizures_at_d14_ok(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY14)
        cleaned_data.update({"recent_seizure": YES})
        form_validator = MentalStatusFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_gcs_lt_15_at_d14_ok(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY14)
        for gcs in [3, 14]:
            with self.subTest(gcs=gcs):
                cleaned_data.update({"glasgow_coma_score": gcs})
                form_validator = MentalStatusFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")
