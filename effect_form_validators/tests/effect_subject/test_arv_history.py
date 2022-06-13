from dateutil.relativedelta import relativedelta
from django import forms
from django.test import TestCase
from django_mock_queries.query import MockModel, MockSet
from edc_constants.constants import NO, NOT_APPLICABLE, YES
from edc_utils import get_utcnow, get_utcnow_as_date

from effect_form_validators.effect_subject import ArvHistoryFormValidator as Base

from ..mixins import FormValidatorTestMixin, TestCaseMixin


class ArvHistoryFormValidator(FormValidatorTestMixin, Base):
    pass


class TestArvHistoryFormValidator(TestCaseMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.arv_regimens_choice_na = MockModel(
            mock_name="ArvRegimens", name=NOT_APPLICABLE, display_name=NOT_APPLICABLE
        )

    def get_cleaned_data(self, **kwargs) -> dict:
        if "report_datetime" not in kwargs:
            kwargs["report_datetime"] = get_utcnow()
        cleaned_data = super().get_cleaned_data(**kwargs)
        cleaned_data.update(
            {
                # HIV Diagnosis
                "hiv_dx_date": get_utcnow_as_date(),
                "hiv_dx_date_estimated": NO,
                # ARV treatment and monitoring
                "on_art_at_crag": NO,
                "ever_on_art": NO,
                "initial_art_date": None,
                "initial_art_date_estimated": NOT_APPLICABLE,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_na),
                "initial_art_regimen_other": "",
                "has_switched_art_regimen": NOT_APPLICABLE,
                "current_art_date": None,
                "current_art_date_estimated": NOT_APPLICABLE,
                "current_art_regimen": MockSet(self.arv_regimens_choice_na),
                "current_art_regimen_other": "",
                # ART adherence
                "has_defaulted": NOT_APPLICABLE,
                "defaulted_date": None,
                "defaulted_date_estimated": NOT_APPLICABLE,
                "is_adherent": NOT_APPLICABLE,
                "art_doses_missed": None,
                # ART decision
                "art_decision": NOT_APPLICABLE,
                # Viral load
                "has_viral_load_result": NO,
                "viral_load_result": None,
                "viral_load_date": None,
                "viral_load_date_estimated": NOT_APPLICABLE,
                # CD4 count
                "has_cd4_result": NO,
                "cd4_result": None,
                "cd4_date": None,
                "cd4_date_estimated": NOT_APPLICABLE,
            }
        )
        return cleaned_data

    def test_cleaned_data_ok(self):
        cleaned_data = self.get_cleaned_data()
        form_validator = ArvHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_arv_history_cd4_date_after_hiv_dx_date_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                # HIV Diagnosis
                "hiv_dx_date": get_utcnow_as_date() - relativedelta(days=7),
                "hiv_dx_date_estimated": NO,
                # CD4 count
                "has_cd4_result": YES,
                "cd4_result": 80,
                "cd4_date": get_utcnow_as_date() - relativedelta(days=6),
                "cd4_date_estimated": NO,
            }
        )
        form_validator = ArvHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_arv_history_cd4_date_on_hiv_dx_date_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                # HIV Diagnosis
                "hiv_dx_date": get_utcnow_as_date(),
                "hiv_dx_date_estimated": NO,
                # CD4 count
                "has_cd4_result": YES,
                "cd4_result": 80,
                "cd4_date": get_utcnow_as_date(),
                "cd4_date_estimated": NO,
            }
        )
        form_validator = ArvHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_arv_history_cd4_date_before_hiv_dx_date_raises(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                # HIV Diagnosis
                "hiv_dx_date": get_utcnow_as_date(),
                "hiv_dx_date_estimated": NO,
                # CD4 count
                "has_cd4_result": YES,
                "cd4_result": 80,
                "cd4_date": get_utcnow_as_date() - relativedelta(days=1),
                "cd4_date_estimated": NO,
            }
        )
        form_validator = ArvHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("cd4_date", cm.exception.error_dict)
        self.assertIn(
            "Invalid. Cannot be before 'HIV diagnosis first known' date",
            cm.exception.error_dict.get("cd4_date")[0].message,
        )
