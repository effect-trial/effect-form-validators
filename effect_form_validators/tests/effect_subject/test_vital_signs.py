from typing import Optional
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django_mock_queries.query import MockModel
from edc_constants.constants import NO, NOT_APPLICABLE, YES
from edc_visit_schedule.constants import DAY01, DAY14

from effect_form_validators.effect_subject import VitalSignsFormValidator as Base

from ..mixins import FormValidatorTestMixin, TestCaseMixin


class VitalSignsMockModel(MockModel):
    @classmethod
    def related_visit_model_attr(cls):
        return "subject_visit"


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
            sys_blood_pressure=120,
            dia_blood_pressure=80,
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
        form_validator = VitalSignsFormValidator(
            cleaned_data=cleaned_data, model=VitalSignsMockModel
        )
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
                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_sys_blood_pressure_required(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        cleaned_data.update(
            sys_blood_pressure=None,
            dia_blood_pressure=80,
        )
        form_validator = VitalSignsFormValidator(
            cleaned_data=cleaned_data, model=VitalSignsMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("sys_blood_pressure", cm.exception.error_dict)
        self.assertIn(
            "This field is required",
            str(cm.exception.error_dict.get("sys_blood_pressure")),
        )

    def test_dia_blood_pressure_required(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        cleaned_data.update(
            sys_blood_pressure=120,
            dia_blood_pressure=None,
        )
        form_validator = VitalSignsFormValidator(
            cleaned_data=cleaned_data, model=VitalSignsMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("dia_blood_pressure", cm.exception.error_dict)
        self.assertIn(
            "This field is required",
            str(cm.exception.error_dict.get("dia_blood_pressure")),
        )

    def test_sys_gte_dia_ok(self):
        self.mock_is_baseline.return_value = False
        for sys, dia in [
            (120, 80),
            (110, 109),
            (80, 80),
        ]:
            with self.subTest(sys=sys, dia=dia):
                cleaned_data = self.get_cleaned_data(visit_code=DAY14)
                cleaned_data.update(
                    sys_blood_pressure=sys,
                    dia_blood_pressure=dia,
                    reportable_as_ae=NO,
                )

                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_sys_lt_dia_raises(self):
        self.mock_is_baseline.return_value = False
        for sys, dia in [
            (80, 120),
            (179, 180),
            (180, 181),
            (181, 182),
            (109, 110),
            (110, 111),
            (111, 112),
        ]:
            with self.subTest(sys=sys, dia=dia):
                cleaned_data = self.get_cleaned_data(visit_code=DAY14)
                cleaned_data.update(
                    sys_blood_pressure=sys,
                    dia_blood_pressure=dia,
                    reportable_as_ae=YES,
                )

                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("dia_blood_pressure", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Diastolic must be less than systolic.",
                    str(cm.exception.error_dict.get("dia_blood_pressure")),
                )

    def test_cannot_proceed_at_baseline_with_severe_htn(self):
        self.mock_is_baseline.return_value = True
        for response in [YES, NO, NOT_APPLICABLE]:
            with self.subTest(reportable_as_ae=response):
                cleaned_data = self.get_cleaned_data(visit_code=DAY01)
                cleaned_data.update(
                    sys_blood_pressure=180,
                    dia_blood_pressure=109,
                    reportable_as_ae=response,
                )

                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("reportable_as_ae", cm.exception.error_dict)

    def test_cannot_proceed_at_baseline_with_gte_g3_fever(self):
        self.mock_is_baseline.return_value = True
        for response in [YES, NO, NOT_APPLICABLE]:
            with self.subTest(reportable_as_ae=response):
                cleaned_data = self.get_cleaned_data(visit_code=DAY01)
                cleaned_data.update(
                    temperature=39.3,
                    reportable_as_ae=response,
                )

                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("reportable_as_ae", cm.exception.error_dict)

    def test_reportable_as_ae_expects_yes_if_severe_htn(self):
        self.mock_is_baseline.return_value = False
        for sys, dia in [
            (181, 111),
            (180, 110),
            (180, 109),
            (179, 110),
            (190, 80),
            (140, 120),
        ]:
            with self.subTest(sys=sys, dia=dia):
                cleaned_data = self.get_cleaned_data(visit_code=DAY14)
                cleaned_data.update(
                    sys_blood_pressure=sys,
                    dia_blood_pressure=dia,
                    reportable_as_ae=NO,
                )

                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("reportable_as_ae", cm.exception.error_dict)
                self.assertIn(
                    (
                        "Invalid. Expected YES. "
                        "Participant has severe hypertension (BP reading >= 180/110mmHg)."
                    ),
                    str(cm.exception.error_dict.get("reportable_as_ae")),
                )

                cleaned_data.update(reportable_as_ae=YES)
                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reportable_as_ae_accepts_yes_no_if_not_severe_htn(self):
        self.mock_is_baseline.return_value = False
        for response in [YES, NO]:
            with self.subTest(reportable_as_ae=response):
                cleaned_data = self.get_cleaned_data(visit_code=DAY14)
                cleaned_data.update(
                    sys_blood_pressure=179,
                    dia_blood_pressure=109,
                    reportable_as_ae=response,
                )

                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reportable_as_ae_expects_yes_if_gte_g3_fever(self):
        self.mock_is_baseline.return_value = False
        for temperature in [39.3, 39.9, 40, 40.1, 45, 46]:
            with self.subTest(temperature=temperature):
                cleaned_data = self.get_cleaned_data(visit_code=DAY14)
                cleaned_data.update(
                    temperature=temperature,
                    reportable_as_ae=NO,
                )

                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("reportable_as_ae", cm.exception.error_dict)
                self.assertIn(
                    (
                        "Invalid. Expected YES. "
                        "Participant has G3 or higher fever (temperature >= 39.3)."
                    ),
                    str(cm.exception.error_dict.get("reportable_as_ae")),
                )

                cleaned_data.update(reportable_as_ae=YES)
                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reportable_as_ae_accepts_yes_no_if_lt_g3_fever(self):
        self.mock_is_baseline.return_value = False
        for response in [YES, NO]:
            with self.subTest(reportable_as_ae=response):
                cleaned_data = self.get_cleaned_data(visit_code=DAY14)
                cleaned_data.update(
                    temperature=39.2,
                    reportable_as_ae=response,
                )

                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
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
                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
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
                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("patient_admitted", cm.exception.error_dict)
                self.assertIn(
                    "Not applicable at baseline",
                    str(cm.exception.error_dict.get("patient_admitted")),
                )

    def test_reportable_as_ae_is_applicable_after_baseline(self):
        self.mock_is_baseline.return_value = False
        for visit_code in self.visit_schedule:
            with self.subTest(visit_code=visit_code):
                cleaned_data = self.get_cleaned_data(
                    visit_code=visit_code,
                    visit_code_sequence=1 if visit_code == DAY01 else 0,
                )
                cleaned_data.update(reportable_as_ae=NOT_APPLICABLE)

                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
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
                        form_validator = VitalSignsFormValidator(
                            cleaned_data=cleaned_data, model=VitalSignsMockModel
                        )
                        try:
                            form_validator.validate()
                        except ValidationError as e:
                            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_patient_admitted_is_applicable_after_baseline(self):
        self.mock_is_baseline.return_value = False
        for visit_code in self.visit_schedule:
            with self.subTest(visit_code=visit_code):
                cleaned_data = self.get_cleaned_data(
                    visit_code=visit_code,
                    visit_code_sequence=1 if visit_code == DAY01 else 0,
                )
                cleaned_data.update(patient_admitted=NOT_APPLICABLE)

                form_validator = VitalSignsFormValidator(
                    cleaned_data=cleaned_data, model=VitalSignsMockModel
                )
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
                        form_validator = VitalSignsFormValidator(
                            cleaned_data=cleaned_data, model=VitalSignsMockModel
                        )
                        try:
                            form_validator.validate()
                        except ValidationError as e:
                            self.fail(f"ValidationError unexpectedly raised. Got {e}")
