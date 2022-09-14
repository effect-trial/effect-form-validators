from typing import Optional
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.test import TestCase, tag
from edc_constants.constants import NO, NOT_APPLICABLE, YES
from edc_utils import formatted_date, get_utcnow
from edc_visit_schedule.constants import DAY01

from effect_form_validators.effect_subject import (
    StudyMedicationBaselineFormValidator as Base,
)

from ..mixins import FormValidatorTestMixin, TestCaseMixin


class StudyMedicationBaselineFormValidator(FormValidatorTestMixin, Base):
    pass


@tag("debug")
class TestStudyMedicationBaselineFormValidation(TestCaseMixin, TestCase):

    flucyt_individual_dose_fields = [
        f"flucyt_dose_{hr}" for hr in ["0400", "1000", "1600", "2200"]
    ]

    def setUp(self) -> None:
        super().setUp()
        sm_baseline_patcher = patch(
            "effect_form_validators.effect_subject"
            ".study_medication_baseline_form_validator.is_baseline"
        )
        self.addCleanup(sm_baseline_patcher.stop)
        self.mock_is_baseline = sm_baseline_patcher.start()

    def get_cleaned_data(
        self,
        visit_code: Optional[str] = None,
        visit_code_sequence: Optional[int] = None,
        **kwargs,
    ) -> dict:
        cleaned_data = super().get_cleaned_data(
            visit_code=visit_code,
            visit_code_sequence=visit_code_sequence,
            report_datetime=kwargs.get("report_datetime", get_utcnow()),
        )
        cleaned_data.update(
            {
                # Flucon
                "flucon_initiated": YES,
                "flucon_not_initiated_reason": "",
                "flucon_dose_datetime": get_utcnow() + relativedelta(minutes=1),
                "flucon_dose_rx": 1200,
                "flucon_notes": "",
                # Flucyt
                "flucyt_initiated": YES,
                "flucyt_not_initiated_reason": "",
                "flucyt_dose_datetime": get_utcnow() + relativedelta(minutes=1),
                "flucyt_dose_expected": 4500,
                "flucyt_dose_rx": 4500,
                "flucyt_dose_0400": 1200,
                "flucyt_dose_1000": 1100,
                "flucyt_dose_1600": 1100,
                "flucyt_dose_2200": 1100,
                "flucyt_notes": "",
            }
        )

        return cleaned_data

    def test_cleaned_data_at_baseline_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_not_at_baseline_raises(self):
        self.mock_is_baseline.return_value = False
        for visit_code in self.visit_schedule:
            for seq in [0, 1, 2]:
                if visit_code == DAY01 and seq == 0:
                    break

                with self.subTest(visit_code=visit_code, visit_code_sequence=seq):
                    cleaned_data = self.get_cleaned_data(
                        visit_code=visit_code, visit_code_sequence=seq
                    )
                    form_validator = StudyMedicationBaselineFormValidator(
                        cleaned_data=cleaned_data
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn("__all__", cm.exception.error_dict)
                    self.assertIn(
                        "This form may only be completed at baseline",
                        str(cm.exception.error_dict.get("__all__")),
                    )

    # Flucon tests
    def test_flucon_not_initiated_reason_required_if_flucon_initiated_no(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_initiated": NO,
                "flucon_not_initiated_reason": "",
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_not_initiated_reason", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucon_not_initiated_reason")),
        )

    def test_flucon_not_initiated_reason_with_flucon_initiated_no_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_initiated": NO,
                "flucon_not_initiated_reason": "Reason flucon not initiated",
                "flucon_dose_datetime": None,
                "flucon_dose_rx": None,
                "flucon_notes": "",
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucon_not_initiated_reason_not_required_if_flucon_initiated_yes(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_initiated": YES,
                "flucon_not_initiated_reason": "Some reason",
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_not_initiated_reason", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("flucon_not_initiated_reason")),
        )

    def test_flucon_dose_datetime_required_if_flucon_initiated_yes(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_initiated": YES,
                "flucon_dose_datetime": None,
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_datetime", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucon_dose_datetime")),
        )

    def test_flucon_dose_datetime_not_required_if_flucon_initiated_no(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_initiated": NO,
                "flucon_not_initiated_reason": "Some reason",
                "flucon_dose_datetime": get_utcnow() + relativedelta(minutes=1),
                "flucon_dose_rx": None,
                "flucon_notes": "",
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_datetime", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("flucon_dose_datetime")),
        )

    def test_flucon_flucyt_dose_datetime_equal_report_datetime_ok(self):
        self.mock_is_baseline.return_value = True
        report_datetime = get_utcnow() - relativedelta(days=14)
        cleaned_data = self.get_cleaned_data(
            visit_code=DAY01,
            visit_code_sequence=0,
            report_datetime=report_datetime,
        )
        cleaned_data.update(
            {
                "flucon_dose_datetime": report_datetime,
                "flucyt_dose_datetime": report_datetime,
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucon_dose_datetime_before_report_datetime_raises(self):
        self.mock_is_baseline.return_value = True
        report_datetime = get_utcnow()
        cleaned_data = self.get_cleaned_data(
            visit_code=DAY01,
            visit_code_sequence=0,
            report_datetime=report_datetime,
        )
        cleaned_data.update({"flucon_dose_datetime": report_datetime - relativedelta(days=1)})
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_datetime", cm.exception.error_dict)
        self.assertIn(
            f"Expected {formatted_date(report_datetime)}",
            str(cm.exception.error_dict.get("flucon_dose_datetime")),
        )

    def test_flucon_dose_datetime_after_report_datetime_raises(self):
        self.mock_is_baseline.return_value = True
        report_datetime = get_utcnow()
        cleaned_data = self.get_cleaned_data(
            visit_code=DAY01,
            visit_code_sequence=0,
            report_datetime=report_datetime,
        )
        cleaned_data.update({"flucon_dose_datetime": report_datetime + relativedelta(days=1)})
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_datetime", cm.exception.error_dict)
        self.assertIn(
            f"Expected {formatted_date(report_datetime)}",
            str(cm.exception.error_dict.get("flucon_dose_datetime")),
        )

    def test_flucon_dose_rx_required_if_flucon_initiated_yes(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_initiated": YES,
                "flucon_dose_rx": None,
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_rx", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucon_dose_rx")),
        )

    def test_flucon_dose_rx_not_required_if_flucon_initiated_no(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_initiated": NO,
                "flucon_not_initiated_reason": "Some reason",
                "flucon_dose_datetime": None,
                "flucon_dose_rx": 1200,
                "flucon_notes": "",
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_rx", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("flucon_dose_rx")),
        )

    def test_flucon_notes_required_baseline_flucon_dose_rx_not_1200(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_initiated": YES,
                "flucon_dose_rx": 800,
                "flucon_notes": "",
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_notes", cm.exception.error_dict)
        self.assertIn(
            "This field is required. Fluconazole dose not 1200 mg/d.",
            str(cm.exception.error_dict.get("flucon_notes")),
        )

    def test_flucon_notes_with_baseline_flucon_dose_rx_1200_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_initiated": YES,
                "flucon_dose_rx": 1200,
                "flucon_notes": "Some other flucon notes here",
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    # Flucyt tests
    def test_flucyt_na_at_baseline_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucyt_initiated": NOT_APPLICABLE,
                "flucyt_not_initiated_reason": "",
                "flucyt_dose_datetime": None,
                "flucyt_dose_expected": None,
                "flucyt_dose_rx": None,
                "flucyt_dose_0400": None,
                "flucyt_dose_1000": None,
                "flucyt_dose_1600": None,
                "flucyt_dose_2200": None,
                "flucyt_notes": "",
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucyt_not_initiated_reason_required_if_flucyt_initiated_no(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucyt_initiated": NO,
                "flucyt_not_initiated_reason": "",
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucyt_not_initiated_reason", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucyt_not_initiated_reason")),
        )

    def test_flucyt_not_initiated_reason_with_flucyt_initiated_no_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucyt_initiated": NO,
                "flucyt_not_initiated_reason": "Reason flucon not initiated",
                "flucyt_dose_datetime": None,
                "flucyt_dose_rx": None,
                "flucyt_dose_0400": None,
                "flucyt_dose_1000": None,
                "flucyt_dose_1600": None,
                "flucyt_dose_2200": None,
                "flucyt_notes": "",
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucyt_not_initiated_reason_not_required_if_flucyt_initiated_not_no(self):
        self.mock_is_baseline.return_value = True
        for answer in [YES, NOT_APPLICABLE]:
            with self.subTest(flucyt_initiated=answer):
                cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
                cleaned_data.update(
                    {
                        "flucyt_initiated": answer,
                        "flucyt_not_initiated_reason": "Some reason",
                    }
                )
                form_validator = StudyMedicationBaselineFormValidator(
                    cleaned_data=cleaned_data
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("flucyt_not_initiated_reason", cm.exception.error_dict)
                self.assertIn(
                    "This field is not required.",
                    str(cm.exception.error_dict.get("flucyt_not_initiated_reason")),
                )

    def test_flucyt_dose_datetime_required_if_flucyt_initiated_yes(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucyt_initiated": YES,
                "flucyt_dose_datetime": None,
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucyt_dose_datetime", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucyt_dose_datetime")),
        )

    def test_flucyt_dose_datetime_not_required_if_flucyt_initiated_not_yes(self):
        self.mock_is_baseline.return_value = True
        for answer in [NO, NOT_APPLICABLE]:
            with self.subTest(flucyt_initiated=answer):
                cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
                cleaned_data.update(
                    {
                        "flucyt_initiated": answer,
                        "flucyt_not_initiated_reason": "Some reason" if answer == NO else "",
                        "flucyt_dose_datetime": get_utcnow() + relativedelta(minutes=1),
                    }
                )
                form_validator = StudyMedicationBaselineFormValidator(
                    cleaned_data=cleaned_data
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("flucyt_dose_datetime", cm.exception.error_dict)
                self.assertIn(
                    "This field is not required.",
                    str(cm.exception.error_dict.get("flucyt_dose_datetime")),
                )

    def test_flucyt_dose_datetime_before_report_datetime_raises(self):
        self.mock_is_baseline.return_value = True
        report_datetime = get_utcnow()
        cleaned_data = self.get_cleaned_data(
            visit_code=DAY01,
            visit_code_sequence=0,
            report_datetime=report_datetime,
        )
        cleaned_data.update({"flucyt_dose_datetime": report_datetime - relativedelta(days=1)})
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucyt_dose_datetime", cm.exception.error_dict)
        self.assertIn(
            f"Expected {formatted_date(report_datetime)}",
            str(cm.exception.error_dict.get("flucyt_dose_datetime")),
        )

    def test_flucyt_dose_datetime_after_report_datetime_raises(self):
        self.mock_is_baseline.return_value = True
        report_datetime = get_utcnow()
        cleaned_data = self.get_cleaned_data(
            visit_code=DAY01,
            visit_code_sequence=0,
            report_datetime=report_datetime,
        )
        cleaned_data.update({"flucyt_dose_datetime": report_datetime + relativedelta(days=1)})
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucyt_dose_datetime", cm.exception.error_dict)
        self.assertIn(
            f"Expected {formatted_date(report_datetime)}",
            str(cm.exception.error_dict.get("flucyt_dose_datetime")),
        )

    def test_flucyt_dose_rx_required_if_flucyt_initiated_yes(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update({"flucyt_dose_rx": None})
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucyt_dose_rx", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucyt_dose_rx")),
        )

    def test_flucyt_dose_rx_not_required_if_flucyt_initiated_not_yes(self):
        self.mock_is_baseline.return_value = True
        for answer in [NO, NOT_APPLICABLE]:
            with self.subTest(flucyt_initiated=answer):
                cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
                cleaned_data.update(
                    {
                        "flucyt_initiated": answer,
                        "flucyt_not_initiated_reason": "Some reason" if answer == NO else "",
                        "flucyt_dose_datetime": None,
                        "flucyt_dose_rx": 100,
                    }
                )
                form_validator = StudyMedicationBaselineFormValidator(
                    cleaned_data=cleaned_data
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("flucyt_dose_rx", cm.exception.error_dict)
                self.assertIn(
                    "This field is not required.",
                    str(cm.exception.error_dict.get("flucyt_dose_rx")),
                )

    def test_individual_flucyt_doses_required_if_flucyt_initiated_yes(self):
        self.mock_is_baseline.return_value = True
        for dose_field in self.flucyt_individual_dose_fields:
            with self.subTest(dose_field=dose_field):
                cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
                cleaned_data.update({dose_field: None})
                form_validator = StudyMedicationBaselineFormValidator(
                    cleaned_data=cleaned_data
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn(dose_field, cm.exception.error_dict)
                self.assertIn(
                    "This field is required.",
                    str(cm.exception.error_dict.get(dose_field)),
                )

    def test_individual_flucyt_doses_not_required_if_flucyt_initiated_not_yes(self):
        self.mock_is_baseline.return_value = True
        for answer in [NO, NOT_APPLICABLE]:
            for dose_field in self.flucyt_individual_dose_fields:
                with self.subTest(answer=answer, dose_field=dose_field):
                    cleaned_data = self.get_cleaned_data(
                        visit_code=DAY01, visit_code_sequence=0
                    )
                    cleaned_data.update(
                        {
                            "flucyt_initiated": answer,
                            "flucyt_not_initiated_reason": "Some reason"
                            if answer == NO
                            else "",
                            "flucyt_dose_datetime": None,
                            "flucyt_dose_rx": None,
                            # Reset all individual doses to None
                            "flucyt_dose_0400": None,
                            "flucyt_dose_1000": None,
                            "flucyt_dose_1600": None,
                            "flucyt_dose_2200": None,
                        }
                    )
                    # Update individual dose being tested
                    cleaned_data.update({dose_field: 1000})
                    form_validator = StudyMedicationBaselineFormValidator(
                        cleaned_data=cleaned_data
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn(dose_field, cm.exception.error_dict)
                    self.assertIn(
                        "This field is not required.",
                        str(cm.exception.error_dict.get(dose_field)),
                    )

    def test_individual_flucyt_doses_can_be_zero_if_flucyt_initiated_yes(self):
        self.mock_is_baseline.return_value = True
        dose_schedules = (
            (0, 2000, 2000, 0),
            (0, 1000, 2000, 1000),
            (1000, 0, 2000, 1000),
            (1000, 1000, 0, 2000),
            (1000, 1000, 2000, 0),
            (4000, 0, 0, 0),
            (0, 4000, 0, 0),
            (0, 0, 4000, 0),
            (0, 0, 0, 4000),
        )
        for schedule in dose_schedules:
            with self.subTest(schedule=schedule):
                dose_0400, dose_1000, dose_1600, dose_2200 = schedule
                cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
                cleaned_data.update(
                    {
                        "flucyt_dose_expected": 4000,
                        "flucyt_dose_rx": 4000,
                        "flucyt_dose_0400": dose_0400,
                        "flucyt_dose_1000": dose_1000,
                        "flucyt_dose_1600": dose_1600,
                        "flucyt_dose_2200": dose_2200,
                    }
                )
                form_validator = StudyMedicationBaselineFormValidator(
                    cleaned_data=cleaned_data
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_individual_flucyt_doses_cannot_be_zero_if_flucyt_initiated_not_yes(self):
        self.mock_is_baseline.return_value = True
        for answer in [NO, NOT_APPLICABLE]:
            for dose_field in self.flucyt_individual_dose_fields:
                with self.subTest(answer=answer, dose_field=dose_field):
                    cleaned_data = self.get_cleaned_data(
                        visit_code=DAY01, visit_code_sequence=0
                    )
                    cleaned_data.update(
                        {
                            "flucyt_initiated": answer,
                            "flucyt_not_initiated_reason": "Some reason"
                            if answer == NO
                            else "",
                            "flucyt_dose_datetime": None,
                            "flucyt_dose_rx": None,
                            # Reset all individual doses to None
                            "flucyt_dose_0400": None,
                            "flucyt_dose_1000": None,
                            "flucyt_dose_1600": None,
                            "flucyt_dose_2200": None,
                        }
                    )
                    # Update individual dose being tested
                    cleaned_data.update({dose_field: 0})
                    form_validator = StudyMedicationBaselineFormValidator(
                        cleaned_data=cleaned_data
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn(dose_field, cm.exception.error_dict)
                    self.assertIn(
                        "This field is not required.",
                        str(cm.exception.error_dict.get(dose_field)),
                    )

    def test_sum_individual_flucyt_doses_eq_flucyt_dose_rx_ok(self):
        self.mock_is_baseline.return_value = True
        dose_schedules = (
            (1000, 1000, 1000, 1000),
            (0, 2000, 2000, 0),
            (500, 1500, 1500, 500),
            (700, 1000, 300, 2000),
        )
        for schedule in dose_schedules:
            with self.subTest(schedule=schedule):
                dose_0400, dose_1000, dose_1600, dose_2200 = schedule
                cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
                cleaned_data.update(
                    {
                        "flucyt_dose_expected": 4000,
                        "flucyt_dose_rx": 4000,
                        "flucyt_dose_0400": dose_0400,
                        "flucyt_dose_1000": dose_1000,
                        "flucyt_dose_1600": dose_1600,
                        "flucyt_dose_2200": dose_2200,
                    }
                )
                form_validator = StudyMedicationBaselineFormValidator(
                    cleaned_data=cleaned_data
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_sum_individual_flucyt_doses_not_eq_flucyt_dose_rx_raises(self):
        self.mock_is_baseline.return_value = True
        dose_schedules = (
            (0, 0, 0, 0),
            (1, 1, 1, 1),
            (1000, 1000, 1000, 999),
            (1001, 1000, 1000, 1000),
            (0, 1000, 1000, 0),
        )
        for schedule in dose_schedules:
            with self.subTest(schedule=schedule):
                dose_0400, dose_1000, dose_1600, dose_2200 = schedule
                cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
                cleaned_data.update(
                    {
                        "flucyt_dose_rx": 4000,
                        "flucyt_dose_0400": dose_0400,
                        "flucyt_dose_1000": dose_1000,
                        "flucyt_dose_1600": dose_1600,
                        "flucyt_dose_2200": dose_2200,
                    }
                )
                form_validator = StudyMedicationBaselineFormValidator(
                    cleaned_data=cleaned_data
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("flucyt_dose_0400", cm.exception.error_dict)
                self.assertIn("flucyt_dose_1000", cm.exception.error_dict)
                self.assertIn("flucyt_dose_1600", cm.exception.error_dict)
                self.assertIn("flucyt_dose_2200", cm.exception.error_dict)
                expected_msg = (
                    "Invalid. "
                    "Expected sum of individual doses to match prescribed flucytosine "
                    "dose (4000 mg/d)."
                )
                self.assertIn(
                    expected_msg, str(cm.exception.error_dict.get("flucyt_dose_0400"))
                )
                self.assertIn(
                    expected_msg, str(cm.exception.error_dict.get("flucyt_dose_1000"))
                )
                self.assertIn(
                    expected_msg, str(cm.exception.error_dict.get("flucyt_dose_1600"))
                )
                self.assertIn(
                    expected_msg, str(cm.exception.error_dict.get("flucyt_dose_2200"))
                )

    def test_flucyt_notes_not_required_if_flucyt_initiated_na(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucyt_initiated": NOT_APPLICABLE,
                "flucyt_dose_datetime": None,
                "flucyt_dose_expected": None,
                "flucyt_dose_rx": None,
                "flucyt_dose_0400": None,
                "flucyt_dose_1000": None,
                "flucyt_dose_1600": None,
                "flucyt_dose_2200": None,
                "flucyt_notes": "Some flucyt notes here",
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucyt_notes", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("flucyt_notes")),
        )

    def test_flucyt_notes_required_if_flucyt_expected_and_rx_differ(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucyt_initiated": YES,
                "flucyt_dose_expected": 4000,
                "flucyt_dose_rx": 4500,
                "flucyt_dose_0400": 1200,
                "flucyt_dose_1000": 1100,
                "flucyt_dose_1600": 1100,
                "flucyt_dose_2200": 1100,
                "flucyt_notes": "",
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucyt_notes", cm.exception.error_dict)
        self.assertIn(
            "This field is required. Flucytosine expected and prescribed doses differ.",
            str(cm.exception.error_dict.get("flucyt_notes")),
        )

    def test_flucyt_notes_with_flucyt_expected_and_rx_identical_ok(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucyt_initiated": YES,
                "flucyt_dose_expected": 4500,
                "flucyt_dose_rx": 4500,
                "flucyt_dose_0400": 1200,
                "flucyt_dose_1000": 1100,
                "flucyt_dose_1600": 1100,
                "flucyt_dose_2200": 1100,
                "flucyt_notes": "Some other flucyt notes here",
            }
        )
        form_validator = StudyMedicationBaselineFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")
