from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django_mock_queries.query import MockModel
from edc_constants.constants import INTERVENTION, OTHER, REFUSED, TOXICITY
from edc_form_validators import FormValidator
from edc_form_validators.tests.mixins import FormValidatorTestMixin
from edc_utils import get_utcnow

from effect_form_validators.effect_subject import (
    FluconMissedDosesFormValidator,
    FlucytMissedDosesFormValidator,
    MissedDosesFormValidatorMixin,
)

from ...mixins import TestCaseMixin
from ...mock_models import AdherenceMockModel


class MissedDosesMockModel(MockModel):
    pass


class MissedDosesTestFormValidator(
    FormValidatorTestMixin, MissedDosesFormValidatorMixin, FormValidator
):
    field = "day_missed"
    reason_field = "missed_reason"
    reason_other_field = "missed_reason_other"
    day_range = range(1, 16)

    def clean(self) -> None:
        self.validate_missed_days()


class TestMissedDosesFormValidatorMixin(TestCaseMixin, TestCase):
    def get_cleaned_data(self, **kwargs) -> dict:
        if "report_datetime" not in kwargs:
            kwargs["report_datetime"] = get_utcnow()
        cleaned_data = super().get_cleaned_data(**kwargs)
        cleaned_data.update(
            {
                "day_missed": None,
                "missed_reason": "",
                "missed_reason_other": "",
            }
        )
        return cleaned_data

    def test_cleaned_data_ok(self):
        cleaned_data = self.get_cleaned_data()
        form_validator = MissedDosesTestFormValidator(
            cleaned_data=cleaned_data, model=MissedDosesMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_missed_dose_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "day_missed": 3,
                "missed_reason": REFUSED,
                "missed_reason_other": "",
            }
        )
        form_validator = MissedDosesTestFormValidator(
            cleaned_data=cleaned_data, model=MissedDosesMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_missed_reason_field_required_if_day_field_selected(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "day_missed": 2,
                "missed_reason": "",
                "missed_reason_other": "",
            }
        )
        form_validator = MissedDosesTestFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("missed_reason", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("missed_reason")),
        )

    def test_missed_reason_field_not_required_if_day_field_not_selected(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "day_missed": None,
                "missed_reason": TOXICITY,
                "missed_reason_other": "",
            }
        )
        form_validator = MissedDosesTestFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("missed_reason", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("missed_reason")),
        )

    def test_missed_reason_other_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "day_missed": 15,
                "missed_reason": OTHER,
                "missed_reason_other": "Some other reason",
            }
        )
        form_validator = MissedDosesTestFormValidator(
            cleaned_data=cleaned_data, model=MissedDosesMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_missed_reason_other_field_required_if_missed_reason_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "day_missed": 15,
                "missed_reason": OTHER,
                "missed_reason_other": "",
            }
        )
        form_validator = MissedDosesTestFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("missed_reason_other", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("missed_reason_other")),
        )

    def test_missed_reason_other_field_not_required_if_missed_reason_not_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "day_missed": 15,
                "missed_reason": TOXICITY,
                "missed_reason_other": "xxx",
            }
        )
        form_validator = MissedDosesTestFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("missed_reason_other", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("missed_reason_other")),
        )


class TestConcreteMissedDosesFormValidators(TestCaseMixin, TestCase):
    missed_dose_validators = [FlucytMissedDosesFormValidator, FluconMissedDosesFormValidator]

    def setUp(self) -> None:
        super().setUp()

        assignment_patcher = patch(
            "effect_form_validators.effect_subject.adherence."
            "flucyt_missed_doses_form_validator.get_assignment_for_subject"
        )
        self.addCleanup(assignment_patcher.stop)
        self.mock_get_assignment_for_subject = assignment_patcher.start()
        self.mock_get_assignment_for_subject.return_value = INTERVENTION

        assignment_descr_patcher = patch(
            "effect_form_validators.effect_subject.adherence."
            "flucyt_missed_doses_form_validator.get_assignment_description_for_subject"
        )
        self.addCleanup(assignment_descr_patcher.stop)
        self.mock_get_assignment_description_for_subject = assignment_descr_patcher.start()
        self.mock_get_assignment_description_for_subject.return_value = (
            "2 weeks fluconazole plus flucytosine"
        )

    def get_cleaned_data(self, form_validator=None, **kwargs) -> dict:
        if "report_datetime" not in kwargs:
            kwargs["report_datetime"] = get_utcnow()
        cleaned_data = super().get_cleaned_data(**kwargs)
        cleaned_data.update(
            {
                "adherence": AdherenceMockModel(subject_identifier=self.subject_identifier),
                "day_missed": None,
                "missed_reason": "",
                "missed_reason_other": "",
            }
        )
        if form_validator and form_validator == FlucytMissedDosesFormValidator:
            cleaned_data.update({"doses_missed": None})

        return cleaned_data

    def test_cleaned_data_ok(self):
        for missed_dose_form_validator in self.missed_dose_validators:
            with self.subTest(fv=missed_dose_form_validator):
                cleaned_data = self.get_cleaned_data(form_validator=missed_dose_form_validator)
                form_validator = missed_dose_form_validator(
                    cleaned_data=cleaned_data, model=MissedDosesMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_missed_dose_ok(self):
        for missed_dose_form_validator in self.missed_dose_validators:
            with self.subTest(fv=missed_dose_form_validator):
                cleaned_data = self.get_cleaned_data(form_validator=missed_dose_form_validator)
                cleaned_data.update(
                    {
                        "day_missed": 3,
                        "missed_reason": REFUSED,
                        "missed_reason_other": "",
                    }
                )
                if missed_dose_form_validator == FlucytMissedDosesFormValidator:
                    cleaned_data.update({"doses_missed": 1})
                form_validator = missed_dose_form_validator(
                    cleaned_data=cleaned_data, model=MissedDosesMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_missed_reason_field_required_if_day_field_selected(self):
        for missed_dose_form_validator in self.missed_dose_validators:
            with self.subTest(fv=missed_dose_form_validator):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "day_missed": 2,
                        "missed_reason": "",
                        "missed_reason_other": "",
                    }
                )
                if missed_dose_form_validator == FlucytMissedDosesFormValidator:
                    cleaned_data.update({"doses_missed": 1})
                form_validator = MissedDosesTestFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("missed_reason", cm.exception.error_dict)
                self.assertIn(
                    "This field is required.",
                    str(cm.exception.error_dict.get("missed_reason")),
                )

    def test_missed_reason_field_not_required_if_day_field_not_selected(self):
        for missed_dose_form_validator in self.missed_dose_validators:
            with self.subTest(fv=missed_dose_form_validator):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "day_missed": None,
                        "missed_reason": TOXICITY,
                        "missed_reason_other": "",
                    }
                )
                if missed_dose_form_validator == FlucytMissedDosesFormValidator:
                    cleaned_data.update({"doses_missed": None})
                form_validator = MissedDosesTestFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("missed_reason", cm.exception.error_dict)
                self.assertIn(
                    "This field is not required.",
                    str(cm.exception.error_dict.get("missed_reason")),
                )

    def test_missed_reason_other_ok(self):
        for missed_dose_form_validator in self.missed_dose_validators:
            with self.subTest(fv=missed_dose_form_validator):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "day_missed": 15,
                        "missed_reason": OTHER,
                        "missed_reason_other": "Some other reason",
                    }
                )
                if missed_dose_form_validator == FlucytMissedDosesFormValidator:
                    cleaned_data.update({"doses_missed": 2})
                form_validator = MissedDosesTestFormValidator(
                    cleaned_data=cleaned_data, model=MissedDosesMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_missed_reason_other_field_required_if_missed_reason_other(self):
        for missed_dose_form_validator in self.missed_dose_validators:
            with self.subTest(fv=missed_dose_form_validator):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "day_missed": 15,
                        "missed_reason": OTHER,
                        "missed_reason_other": "",
                    }
                )
                if missed_dose_form_validator == FlucytMissedDosesFormValidator:
                    cleaned_data.update({"doses_missed": 3})
                form_validator = MissedDosesTestFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("missed_reason_other", cm.exception.error_dict)
                self.assertIn(
                    "This field is required.",
                    str(cm.exception.error_dict.get("missed_reason_other")),
                )

    def test_missed_reason_other_field_not_required_if_missed_reason_not_other(self):
        for missed_dose_form_validator in self.missed_dose_validators:
            with self.subTest(fv=missed_dose_form_validator):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "day_missed": 15,
                        "missed_reason": TOXICITY,
                        "missed_reason_other": "xxx",
                    }
                )
                if missed_dose_form_validator == FlucytMissedDosesFormValidator:
                    cleaned_data.update({"doses_missed": 4})
                form_validator = MissedDosesTestFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("missed_reason_other", cm.exception.error_dict)
                self.assertIn(
                    "This field is not required.",
                    str(cm.exception.error_dict.get("missed_reason_other")),
                )
