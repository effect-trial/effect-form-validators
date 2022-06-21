from django.core.exceptions import ValidationError
from django.test import TestCase
from django_mock_queries.query import MockModel
from edc_constants.constants import NO, NOT_APPLICABLE, OTHER, YES

from effect_form_validators.effect_subject import PatientHistoryFormValidator as Base

from ..mixins import FormValidatorTestMixin, TestCaseMixin


class PatientHistoryFormValidator(FormValidatorTestMixin, Base):
    pass


class TestPatientHistoryFormValidator(TestCaseMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.medications_choice_na = MockModel(
            mock_name="Medication", name=NOT_APPLICABLE, display_name=NOT_APPLICABLE
        )

    def get_cleaned_data(self, **kwargs) -> dict:
        cleaned_data = super().get_cleaned_data(**kwargs)
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": NO,
                "flucon_days": None,
                "flucon_dose": NOT_APPLICABLE,
                "flucon_dose_other": None,
                "flucon_dose_other_reason": "",
                "reported_neuro_abnormality": NO,
                "neuro_abnormality_details": "",
                "tb_prev_dx": NO,
                "tb_site": NOT_APPLICABLE,
                "on_tb_tx": NOT_APPLICABLE,
                "tb_dx_ago": NOT_APPLICABLE,
                "on_rifampicin": NOT_APPLICABLE,
                "rifampicin_start_date": None,
                "previous_oi": NO,
                "previous_oi_name": "",
                "previous_oi_dx_date": None,
                "any_medications": NO,
                "specify_medications": None,
                "specify_steroid_other": "",
                "specify_medications_other": "",
            }
        )
        return cleaned_data

    def test_cleaned_data_ok(self):
        cleaned_data = self.get_cleaned_data()
        form_validator = PatientHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucon_days_required_if_flucon_1w_prior_rando_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": YES,
                "flucon_days": None,
            }
        )
        form_validator = PatientHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_days", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucon_days")),
        )

        cleaned_data.update(
            {
                "flucon_days": 6,
                "flucon_dose": "1200_mg_d",
            }
        )
        form_validator = PatientHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucon_days_not_required_if_flucon_1w_prior_rando_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": NO,
                "flucon_days": 2,
            }
        )
        form_validator = PatientHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_days", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("flucon_days")),
        )

    def test_flucon_dose_applicable_if_flucon_1w_prior_rando_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": YES,
                "flucon_days": 1,
                "flucon_dose": NOT_APPLICABLE,
            }
        )
        form_validator = PatientHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("flucon_dose")),
        )

        cleaned_data.update(
            {
                "flucon_dose": "800_mg_d",
            }
        )
        form_validator = PatientHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucon_dose_not_applicable_if_flucon_1w_prior_rando_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": NO,
                "flucon_days": None,
                "flucon_dose": "800_mg_d",
            }
        )
        form_validator = PatientHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose", cm.exception.error_dict)
        self.assertIn(
            "This field is not applicable.",
            str(cm.exception.error_dict.get("flucon_dose")),
        )

    def test_flucon_dose_other_required_if_flucon_dose_is_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": YES,
                "flucon_days": 7,
                "flucon_dose": OTHER,
                "flucon_dose_other": None,
            }
        )
        form_validator = PatientHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_other", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucon_dose_other")),
        )

        cleaned_data.update(
            {
                "flucon_dose_other": 400,
                "flucon_dose_other_reason": "reason for other dose",
            }
        )
        form_validator = PatientHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucon_dose_other_not_required_if_flucon_dose_is_not_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": YES,
                "flucon_days": 1,
                "flucon_dose": "800_mg_d",
                "flucon_dose_other": 400,
            }
        )
        form_validator = PatientHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_other", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("flucon_dose_other")),
        )

    def test_flucon_dose_other_reason_required_if_flucon_dose_is_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": YES,
                "flucon_days": 7,
                "flucon_dose": OTHER,
                "flucon_dose_other": 400,
                "flucon_dose_other_reason": "",
            }
        )
        form_validator = PatientHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_other_reason", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucon_dose_other_reason")),
        )

        cleaned_data.update(
            {
                "flucon_dose_other_reason": "reason for other dose",
            }
        )
        form_validator = PatientHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucon_dose_other_reason_not_required_if_flucon_dose_is_not_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": YES,
                "flucon_days": 1,
                "flucon_dose": "800_mg_d",
                "flucon_dose_other": None,
                "flucon_dose_other_reason": "Some other reason",
            }
        )
        form_validator = PatientHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_other_reason", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("flucon_dose_other_reason")),
        )
