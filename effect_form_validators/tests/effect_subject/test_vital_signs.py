from typing import Optional
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.test import TestCase
from edc_constants.constants import NO, NOT_APPLICABLE, YES
from edc_visit_schedule.constants import DAY01, DAY14

from effect_form_validators.effect_subject import VitalSignsFormValidator as Base

from ..mixins import FormValidatorTestMixin, TestCaseMixin


class VitalSignsFormValidator(FormValidatorTestMixin, Base):
    pass


class TestVitalSignsFormValidator(TestCaseMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        patcher = patch(
            "effect_form_validators.effect_subject.vital_signs_form_validator.is_baseline"
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
        baseline = (
            cleaned_data.get("subject_visit").visit_code == DAY01
            and cleaned_data.get("subject_visit").visit_code_sequence == 0
        )
        cleaned_data.update(
            weight=60.0,
            weight_measured_or_est="measured",
            heart_rate=60,
            respiratory_rate=14,
            temperature=37.0,
            reportable_as_ae=NOT_APPLICABLE if baseline else NO,
            patient_admitted=NOT_APPLICABLE if baseline else NO,
        )
        return cleaned_data

    def test_cleaned_data_at_baseline_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_cleaned_data_after_baseline_ok(self):
        self.mock_is_baseline.return_value = False
        for visit_code in self.visit_schedule:
            with self.subTest(visit_code=visit_code):
                cleaned_data = self.get_cleaned_data(
                    visit_code=visit_code,
                    visit_code_sequence=1 if visit_code == DAY01 else 0,
                )
                form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reportable_as_ae_not_applicable_at_baseline(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        for response in [YES, NO]:
            with self.subTest(reportable_as_ae=response):
                cleaned_data.update(reportable_as_ae=response)
                form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
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
                cleaned_data.update(patient_admitted=response)
                form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("patient_admitted", cm.exception.error_dict)
                self.assertIn(
                    "Not applicable at baseline",
                    str(cm.exception.error_dict.get("patient_admitted")),
                )

    def test_reportable_as_ae_is_applicable_if_not_baseline(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(
            visit_code=DAY14,
            report_datetime=self.consent_datetime + relativedelta(days=14),
        )
        cleaned_data.update(reportable_as_ae=NOT_APPLICABLE)

        form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("reportable_as_ae", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable",
            str(cm.exception.error_dict.get("reportable_as_ae")),
        )

        for response in [YES, NO]:
            with self.subTest(reportable_as_ae=response):
                cleaned_data.update(reportable_as_ae=response)
                form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_patient_admitted_is_applicable_if_not_baseline(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(
            visit_code=DAY14,
            report_datetime=self.consent_datetime + relativedelta(days=14),
        )
        cleaned_data.update(patient_admitted=NOT_APPLICABLE)

        form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("patient_admitted", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable",
            str(cm.exception.error_dict.get("patient_admitted")),
        )

        for response in [YES, NO]:
            with self.subTest(patient_admitted=response):
                cleaned_data.update(patient_admitted=response)
                form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")
