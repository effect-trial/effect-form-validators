from dateutil.relativedelta import relativedelta
from django import forms
from django.core.exceptions import ValidationError
from django.test import TestCase
from edc_constants.constants import FEMALE, NEG, NO, NOT_APPLICABLE, POS, YES
from edc_form_validators import FormValidatorTestCaseMixin
from edc_utils import get_utcnow, get_utcnow_as_date

from effect_form_validators.effect_screening import (
    SubjectScreeningFormValidator as Base,
)
from effect_form_validators.tests.mixins import FormValidatorTestMixin, TestCaseMixin


class SubjectScreeningFormValidator(FormValidatorTestMixin, Base):
    pass


class TestSubjectScreeningForm(FormValidatorTestCaseMixin, TestCaseMixin, TestCase):

    form_validator_default_form_cls = SubjectScreeningFormValidator
    ELIGIBLE_CD4_VALUE = 99

    def get_cleaned_data(self, **kwargs) -> dict:
        return {
            "report_datetime": get_utcnow(),
            "initials": "EW",
            "gender": FEMALE,
            "age_in_years": 25,
            "hiv_pos": YES,
            "hiv_confirmed_date": get_utcnow_as_date() - relativedelta(days=30),
            "hiv_confirmed_method": "historical_lab_result",
            "cd4_value": self.ELIGIBLE_CD4_VALUE,
            "cd4_date": get_utcnow_as_date() - relativedelta(days=7),
            "serum_crag_value": POS,
            "serum_crag_date": get_utcnow_as_date() - relativedelta(days=6),
            "lp_done": YES,
            "lp_date": get_utcnow_as_date() - relativedelta(days=6),
            "lp_declined": NOT_APPLICABLE,
            "csf_crag_value": NEG,
            "cm_in_csf": NO,
            "cm_in_csf_date": None,
            "cm_in_csf_method:": NOT_APPLICABLE,
            "cm_in_csf_method_other": "",
            "prior_cm_episode": NO,
            "reaction_to_study_drugs": NO,
            "on_flucon": NO,
            "contraindicated_meds": NO,
            "mg_severe_headache": NO,
            "mg_headache_nuchal_rigidity": NO,
            "mg_headache_vomiting": NO,
            "mg_seizures": NO,
            "mg_gcs_lt_15": NO,
            "any_other_mg_ssx": NO,
            "any_other_mg_ssx_other": "",
            "jaundice": NO,
            "pregnant": NOT_APPLICABLE,
            "preg_test_date": None,
            "breast_feeding": NO,
            "willing_to_participate": YES,
            "consent_ability": YES,
            "unsuitable_for_study": NO,
            "reasons_unsuitable": "",
            "unsuitable_agreed": NOT_APPLICABLE,
        }

    def test_cleaned_data_ok(self):
        cleaned_data = self.get_cleaned_data()
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_hiv_confirmed_date_required_if_hiv_pos_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "hiv_pos": YES,
                "hiv_confirmed_date": None,
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("hiv_confirmed_date", cm.exception.error_dict)
        self.assertEqual(
            {"hiv_confirmed_date": ["This field is required."]},
            cm.exception.message_dict,
        )

    def test_hiv_confirmed_date_ok_if_hiv_pos_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "hiv_pos": YES,
                "hiv_confirmed_date": cleaned_data.get("cd4_date"),
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_hiv_confirmed_date_not_required_if_hiv_pos_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "hiv_pos": NO,
                "hiv_confirmed_date": get_utcnow_as_date(),
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("hiv_confirmed_date", cm.exception.error_dict)
        self.assertEqual(
            {"hiv_confirmed_date": ["This field is not required."]},
            cm.exception.message_dict,
        )

    def test_hiv_confirmed_method_applicable_if_hiv_pos_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "hiv_pos": YES,
                "hiv_confirmed_date": get_utcnow_as_date() - relativedelta(days=30),
                "hiv_confirmed_method": NOT_APPLICABLE,
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("hiv_confirmed_method", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable",
            cm.exception.error_dict.get("hiv_confirmed_method")[0].message,
        )

    def test_hiv_confirmed_method_not_applicable_if_hiv_pos_no(self):
        for hiv_confirmed_method_response in ["site_rapid_test", "historical_lab_result"]:
            with self.subTest(hiv_confirmed_method_response=hiv_confirmed_method_response):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "hiv_pos": NO,
                        "hiv_confirmed_date": None,
                        "hiv_confirmed_method": hiv_confirmed_method_response,
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("hiv_confirmed_method", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable",
                    cm.exception.error_dict.get("hiv_confirmed_method")[0].message,
                )

    def test_cd4_date_before_on_after_hiv_confirmed_date_ok(self):
        for cd4_days_ago in [8, 7, 6]:
            with self.subTest(cd4_days_ago=cd4_days_ago):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "hiv_pos": YES,
                        "hiv_confirmed_date": get_utcnow_as_date() - relativedelta(days=7),
                        "cd4_value": self.ELIGIBLE_CD4_VALUE,
                        "cd4_date": get_utcnow_as_date() - relativedelta(days=cd4_days_ago),
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except forms.ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")
