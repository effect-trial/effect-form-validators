from dateutil.relativedelta import relativedelta
from django import forms
from django.test import TestCase
from edc_consent.constants import HOSPITAL_NUMBER
from edc_constants.constants import FEMALE, NO, NOT_APPLICABLE, YES
from edc_form_validators import FormValidatorTestCaseMixin
from edc_form_validators.tests.mixins import FormValidatorTestMixin
from edc_utils import get_utcnow

from effect_form_validators.effect_consent import SubjectConsentFormValidator as Base

from ..mixins import TestCaseMixin


class SubjectConsentFormValidator(FormValidatorTestMixin, Base):
    pass


class TestHospitalizationFormValidation(FormValidatorTestCaseMixin, TestCaseMixin, TestCase):
    form_validator_cls = SubjectConsentFormValidator

    def get_consent_v1_cleaned_data(self, **kwargs) -> dict:
        cleaned_data = super().get_cleaned_data(**kwargs)
        cleaned_data.update(
            {
                "screening_identifier": "SX123",
                "first_name": "JANE",
                "last_name": "DOE",
                "initials": "JD",
                "gender": FEMALE,
                "language": "sw",
                "is_able": YES,
                "is_literate": YES,
                "witness_name": None,
                "consent_datetime": get_utcnow(),
                "dob": get_utcnow().date() - relativedelta(years=20),
                "is_dob_estimated": "D",
                "identity": "12345",
                "identity_type": HOSPITAL_NUMBER,
                "confirm_identity": "12345",
                "is_incarcerated": NO,
                "consent_reviewed": YES,
                "study_questions": YES,
                "assessment_score": YES,
                "consent_signature": YES,
                "consent_copy": YES,
            }
        )
        return cleaned_data

    def get_consent_v2_cleaned_data(self, **kwargs):
        cleaned_data = self.get_consent_v1_cleaned_data(**kwargs)
        cleaned_data.update(
            {
                "he_substudy": NO,
                "sample_storage": NO,
                "sample_export": NOT_APPLICABLE,
                "hcw_data_sharing": NO,
            }
        )
        return cleaned_data

    def test_consent_v1_cleaned_data_ok(self):
        cleaned_data = self.get_consent_v1_cleaned_data()
        form_validator = SubjectConsentFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_consent_v2_cleaned_data_ok(self):
        cleaned_data = self.get_consent_v2_cleaned_data()
        form_validator = SubjectConsentFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_consent_v2_sample_export_applicable_if_sample_storage_yes(self):
        cleaned_data = self.get_consent_v2_cleaned_data()
        cleaned_data.update(
            {
                "sample_storage": YES,
                "sample_export": NOT_APPLICABLE,
            }
        )

        form_validator = SubjectConsentFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("sample_export", cm.exception.error_dict)
        self.assertEqual(
            {"sample_export": ["This field is applicable."]},
            cm.exception.message_dict,
        )

    def test_consent_v2_sample_export_not_applicable_if_sample_storage_no(self):
        for export_response in [YES, NO]:
            with self.subTest(answ=export_response):
                cleaned_data = self.get_consent_v2_cleaned_data()
                cleaned_data.update(
                    {
                        "sample_storage": NO,
                        "sample_export": export_response,
                    }
                )
                form_validator = SubjectConsentFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("sample_export", cm.exception.error_dict)
                self.assertEqual(
                    {"sample_export": ["This field is not applicable."]},
                    cm.exception.message_dict,
                )

            cleaned_data.update({"sample_export": NOT_APPLICABLE})
            form_validator = SubjectConsentFormValidator(cleaned_data=cleaned_data)
            try:
                form_validator.validate()
            except forms.ValidationError as e:
                self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_consent_v2_sample_export_response_with_sample_storage_yes_ok(self):
        for export_response in [YES, NO]:
            with self.subTest(answ=export_response):
                cleaned_data = self.get_consent_v2_cleaned_data()
                cleaned_data.update(
                    {
                        "sample_storage": YES,
                        "sample_export": export_response,
                    }
                )
                form_validator = SubjectConsentFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except forms.ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_consent_v2_consent_all_ok(self):
        cleaned_data = self.get_consent_v2_cleaned_data()
        cleaned_data.update(
            {
                "he_substudy": YES,
                "sample_storage": YES,
                "sample_export": YES,
                "hcw_data_sharing": YES,
            }
        )
        form_validator = SubjectConsentFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")
