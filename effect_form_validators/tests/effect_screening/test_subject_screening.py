from dateutil.relativedelta import relativedelta
from django import forms
from django.core.exceptions import ValidationError
from django.test import TestCase
from edc_constants.constants import (
    DECEASED,
    FEMALE,
    MALE,
    NEG,
    NO,
    NOT_APPLICABLE,
    NOT_DONE,
    NOT_EVALUATED,
    OTHER,
    PENDING,
    POS,
    YES,
)
from edc_form_validators import FormValidatorTestCaseMixin
from edc_form_validators.tests.mixins import FormValidatorTestMixin
from edc_utils import get_utcnow, get_utcnow_as_date

from effect_form_validators.constants import UNABLE_TO_CONTACT
from effect_form_validators.effect_screening import (
    SubjectScreeningFormValidator as Base,
)

from ..mixins import TestCaseMixin


class SubjectScreeningFormValidator(FormValidatorTestMixin, Base):
    pass


class TestSubjectScreeningForm(FormValidatorTestCaseMixin, TestCaseMixin, TestCase):
    form_validator_cls = SubjectScreeningFormValidator
    ELIGIBLE_CD4_VALUE = 99

    def get_cleaned_data(self, **kwargs) -> dict:
        return {
            "report_datetime": get_utcnow(),
            "initials": "EW",
            "gender": FEMALE,
            "age_in_years": 25,
            "parent_guardian_consent": NOT_APPLICABLE,
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
            "unsuitable_reason": NOT_APPLICABLE,
            "unsuitable_reason_other": "",
            "unsuitable_agreed": NOT_APPLICABLE,
        }

    def test_cleaned_data_ok(self):
        cleaned_data = self.get_cleaned_data()
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_age_in_years_lt_0_raises(self):
        for age in [-1, -2, -20]:
            for consent_answ in [YES, NO, NOT_APPLICABLE]:
                with self.subTest(age=age, consent_answ=consent_answ):
                    cleaned_data = self.get_cleaned_data()
                    cleaned_data.update(
                        {
                            "age_in_years": age,
                            "parent_guardian_consent": consent_answ,
                        }
                    )
                    form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn("age_in_years", cm.exception.error_dict)
                    self.assertIn(
                        "Invalid. Please enter a valid age in years.",
                        str(cm.exception.error_dict.get("age_in_years")),
                    )

    def test_age_in_years_gte_120_raises(self):
        for age in [120, 121, 122, 200, 999]:
            for consent_answ in [YES, NO, NOT_APPLICABLE]:
                with self.subTest(age=age, consent_answ=consent_answ):
                    cleaned_data = self.get_cleaned_data()
                    cleaned_data.update(
                        {
                            "age_in_years": age,
                            "parent_guardian_consent": consent_answ,
                        }
                    )
                    form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn("age_in_years", cm.exception.error_dict)
                    self.assertIn(
                        "Invalid. Please enter a valid age in years.",
                        str(cm.exception.error_dict.get("age_in_years")),
                    )

    def test_age_in_years_gte_18_ok(self):
        for age in [18, 19, 29, 99, 119]:
            with self.subTest(age=age):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "age_in_years": age,
                        "parent_guardian_consent": NOT_APPLICABLE,
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_parent_guardian_consent_applicable_if_age_in_years_lt_18(self):
        for age in [17, 16, 13, 12, 10, 1, 0]:
            with self.subTest(age=age):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "age_in_years": age,
                        "parent_guardian_consent": NOT_APPLICABLE,
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("parent_guardian_consent", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("parent_guardian_consent")),
                )

    def test_age_in_years_lt_18_without_consent_yes_raises(self):
        for age in [17, 16, 13, 12, 10, 1, 0]:
            with self.subTest(age=age):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "age_in_years": age,
                        "parent_guardian_consent": NO,
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("parent_guardian_consent", cm.exception.error_dict)
                self.assertIn(
                    "STOP. You must have consent from parent",
                    str(cm.exception.error_dict.get("parent_guardian_consent")),
                )

    def test_age_in_years_lt_18_with_consent_yes_ok(self):
        for age in [17, 16, 13, 12, 11, 10, 5, 1, 0]:
            with self.subTest(age=age):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "age_in_years": age,
                        "parent_guardian_consent": YES,
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_age_in_years_gte_18_doesnt_require_consent(self):
        for age in [18, 19, 29, 99, 119]:
            for consent_answ in [YES, NO]:
                with self.subTest(age=age, consent_answ=consent_answ):
                    cleaned_data = self.get_cleaned_data()
                    cleaned_data.update(
                        {
                            "age_in_years": age,
                            "parent_guardian_consent": consent_answ,
                        }
                    )
                    form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn("parent_guardian_consent", cm.exception.error_dict)
                    self.assertIn(
                        "This field is not applicable.",
                        str(cm.exception.error_dict.get("parent_guardian_consent")),
                    )

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

    def test_cd4_date_after_report_date_raises(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "report_datetime": get_utcnow(),
                "cd4_value": self.ELIGIBLE_CD4_VALUE,
                "cd4_date": get_utcnow_as_date() + relativedelta(days=1),
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("cd4_date", cm.exception.error_dict)
        self.assertIn(
            "Invalid. Must be on or before report date/time. Got",
            str(cm.exception.error_dict.get("cd4_date")),
        )

    def test_cd4_date_gt_21_days_before_report_date_ok(self):
        for days in [22, 30, 60, 365]:
            with self.subTest(days_after=days):
                cleaned_data = self.get_cleaned_data()
                report_datetime = get_utcnow() - relativedelta(days=7)
                cleaned_data.update(
                    {
                        "report_datetime": report_datetime,
                        "cd4_value": self.ELIGIBLE_CD4_VALUE,
                        "cd4_date": report_datetime.date() - relativedelta(days=days),
                        "serum_crag_date": (
                            report_datetime.date() - relativedelta(days=days - 1)
                        ),
                        "lp_date": report_datetime.date() - relativedelta(days=days - 1),
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except forms.ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

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

    def test_serum_crag_negative_raises(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "serum_crag_value": NEG,
                "serum_crag_date": get_utcnow_as_date() - relativedelta(days=1),
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("serum_crag_value", cm.exception.error_dict)
        self.assertIn(
            "Invalid. Subject must have positive serum/plasma CrAg test result.",
            str(cm.exception.error_dict.get("serum_crag_value")),
        )

    def test_serum_crag_positive_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "serum_crag_value": POS,
                "serum_crag_date": get_utcnow_as_date() - relativedelta(days=2),
                "lp_done": YES,
                "lp_date": get_utcnow_as_date() - relativedelta(days=2),
                "lp_declined": NOT_APPLICABLE,
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_serum_crag_before_cd4_date_now_ok(self):
        # test when eligible
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "cd4_value": self.ELIGIBLE_CD4_VALUE,
                "cd4_date": get_utcnow_as_date() - relativedelta(days=7),
                "serum_crag_value": POS,
                "serum_crag_date": get_utcnow_as_date() - relativedelta(days=8),
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

        # test can still save when ineligible
        cd4_date = get_utcnow_as_date() - relativedelta(days=61)
        cleaned_data.update(
            {
                "cd4_value": self.ELIGIBLE_CD4_VALUE,
                "cd4_date": cd4_date,
                "serum_crag_value": POS,
                "serum_crag_date": cd4_date - relativedelta(days=30),
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_serum_crag_gt_21_days_before_cd4_date_ok(self):
        for days in [-90, -60, -30, -22]:
            with self.subTest(days_after=days):
                cleaned_data = self.get_cleaned_data()
                cd4_date = get_utcnow_as_date() - relativedelta(days=7)
                cleaned_data.update(
                    {
                        "cd4_value": self.ELIGIBLE_CD4_VALUE,
                        "cd4_date": cd4_date,
                        "serum_crag_value": POS,
                        "serum_crag_date": cd4_date + relativedelta(days=days),
                        # avoid anything that will trigger lp validation
                        "lp_done": NO,
                        "lp_date": None,
                        "lp_declined": YES,
                        "csf_crag_value": NOT_APPLICABLE,
                        "cm_in_csf": NOT_APPLICABLE,
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_serum_crag_gt_21_days_after_cd4_date_ok(self):
        for days in [22, 30, 60, 90]:
            with self.subTest(days_after=days):
                cleaned_data = self.get_cleaned_data()
                cd4_date = get_utcnow_as_date() - relativedelta(days=7)
                serum_crag_date = cd4_date + relativedelta(days=days)
                report_datetime = serum_crag_date + relativedelta(days=1)
                cleaned_data.update(
                    {
                        "report_datetime": report_datetime,
                        "cd4_value": self.ELIGIBLE_CD4_VALUE,
                        "cd4_date": cd4_date,
                        "serum_crag_value": POS,
                        "serum_crag_date": serum_crag_date,
                        # avoid anything that will trigger lp validation
                        "lp_done": NO,
                        "lp_date": None,
                        "lp_declined": YES,
                        "csf_crag_value": NOT_APPLICABLE,
                        "cm_in_csf": NOT_APPLICABLE,
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_serum_crag_lte_21_days_before_report_date_ok(self):
        for days in [21, 14, 13, 1, 0]:
            with self.subTest(days_before=days):
                cleaned_data = self.get_cleaned_data()
                report_datetime = get_utcnow()
                cleaned_data.update(
                    {
                        "report_datetime": report_datetime,
                        "cd4_value": self.ELIGIBLE_CD4_VALUE,
                        "cd4_date": report_datetime.date() - relativedelta(days=days),
                        "serum_crag_value": POS,
                        "serum_crag_date": report_datetime.date() - relativedelta(days=days),
                        "lp_date": report_datetime.date() - relativedelta(days=days),
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_serum_crag_gt_21_days_before_report_date_ok(self):
        for days in [22, 25, 30]:
            with self.subTest(days_before=days):
                cleaned_data = self.get_cleaned_data()
                report_datetime = get_utcnow()
                cleaned_data.update(
                    {
                        "report_datetime": report_datetime,
                        "cd4_value": self.ELIGIBLE_CD4_VALUE,
                        "cd4_date": report_datetime.date() - relativedelta(days=days),
                        "serum_crag_value": POS,
                        "serum_crag_date": report_datetime.date() - relativedelta(days=days),
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_lp_date_gt_3_days_before_serum_crag_date_raises(self):
        for days_before in [4, 14, 21]:
            with self.subTest(days_before=days_before):
                cleaned_data = self.get_cleaned_data()
                serum_crag_date = cleaned_data.get("report_datetime").date()
                cleaned_data.update(
                    {
                        "cd4_value": self.ELIGIBLE_CD4_VALUE,
                        "cd4_date": serum_crag_date,
                        "serum_crag_value": POS,
                        "serum_crag_date": serum_crag_date,
                        "lp_done": YES,
                        "lp_date": serum_crag_date - relativedelta(days=days_before),
                        "lp_declined": NOT_APPLICABLE,
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("lp_date", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. LP cannot be more than 3 days before serum/plasma CrAg date",
                    str(cm.exception.error_dict.get("lp_date")),
                )

    def test_lp_date_lte_3_days_before_serum_crag_date_ok(self):
        for days_before in [1, 2, 3]:
            with self.subTest(days_before=days_before):
                cleaned_data = self.get_cleaned_data()
                serum_crag_date = cleaned_data.get("report_datetime").date()
                cleaned_data.update(
                    {
                        "cd4_value": self.ELIGIBLE_CD4_VALUE,
                        "cd4_date": serum_crag_date,
                        "serum_crag_value": POS,
                        "serum_crag_date": serum_crag_date,
                        "lp_done": YES,
                        "lp_date": serum_crag_date - relativedelta(days=days_before),
                        "lp_declined": NOT_APPLICABLE,
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_lp_date_on_serum_crag_date_ok(self):
        cleaned_data = self.get_cleaned_data()
        serum_crag_date = cleaned_data.get("report_datetime").date()
        cleaned_data.update(
            {
                "cd4_value": self.ELIGIBLE_CD4_VALUE,
                "cd4_date": serum_crag_date,
                "serum_crag_value": POS,
                "serum_crag_date": serum_crag_date,
                "lp_done": YES,
                "lp_date": serum_crag_date,
                "lp_declined": NOT_APPLICABLE,
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_lp_date_after_report_date_raises(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "cd4_value": self.ELIGIBLE_CD4_VALUE,
                "cd4_date": cleaned_data.get("report_datetime").date(),
                "serum_crag_value": POS,
                "serum_crag_date": cleaned_data.get("report_datetime").date(),
                "lp_done": YES,
                "lp_date": cleaned_data.get("report_datetime").date() + relativedelta(days=1),
                "lp_declined": NOT_APPLICABLE,
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("lp_date", cm.exception.error_dict)
        self.assertIn(
            "Invalid. Must be on or before report date/time. Got",
            str(cm.exception.error_dict.get("lp_date")),
        )

    def test_lp_date_on_report_date_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "cd4_value": self.ELIGIBLE_CD4_VALUE,
                "cd4_date": cleaned_data.get("report_datetime").date(),
                "serum_crag_value": POS,
                "serum_crag_date": cleaned_data.get("report_datetime").date(),
                "lp_done": YES,
                "lp_date": cleaned_data.get("report_datetime").date(),
                "lp_declined": NOT_APPLICABLE,
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_csf_crag_value_not_applicable_if_lp_done_no(self):
        for csf_crag_value in [POS, NEG, PENDING, NOT_DONE]:
            with self.subTest(csf_crag_value):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "lp_done": NO,
                        "lp_date": None,
                        "lp_declined": YES,
                        "csf_crag_value": csf_crag_value,
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("csf_crag_value", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable.",
                    str(cm.exception.error_dict.get("csf_crag_value")),
                )

    def test_csf_crag_value_applicable_if_lp_done_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "lp_done": YES,
                "lp_date": cleaned_data.get("report_datetime").date(),
                "lp_declined": NOT_APPLICABLE,
                "csf_crag_value": NOT_APPLICABLE,
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("csf_crag_value", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("csf_crag_value")),
        )

    def test_csf_crag_value_ok_if_lp_done_yes(self):
        for csf_crag_value in [POS, NEG, PENDING, NOT_DONE]:
            with self.subTest(csf_crag_value=csf_crag_value):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "lp_done": YES,
                        "lp_date": cleaned_data.get("report_datetime").date(),
                        "lp_declined": NOT_APPLICABLE,
                        "csf_crag_value": csf_crag_value,
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_cm_in_csf_date_before_lp_date_raises(self):
        for days in [1, 2, 10]:
            with self.subTest(days_before=days):
                cleaned_data = self.get_cleaned_data()
                lp_date = cleaned_data.get("report_datetime").date()
                cleaned_data.update(
                    {
                        "cd4_value": self.ELIGIBLE_CD4_VALUE,
                        "cd4_date": lp_date,
                        "serum_crag_value": POS,
                        "serum_crag_date": lp_date,
                        "lp_done": YES,
                        "lp_date": lp_date,
                        "lp_declined": NOT_APPLICABLE,
                        "cm_in_csf": PENDING,
                        "cm_in_csf_date": lp_date - relativedelta(days=days),
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("cm_in_csf_date", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Cannot be before LP date",
                    str(cm.exception.error_dict.get("cm_in_csf_date")),
                )

    def test_cm_in_csf_date_on_after_lp_date_ok(self):
        for days in [0, 1, 2, 10]:
            with self.subTest(days_after=days):
                cleaned_data = self.get_cleaned_data()
                lp_date = cleaned_data.get("report_datetime").date()
                cleaned_data.update(
                    {
                        "cd4_value": self.ELIGIBLE_CD4_VALUE,
                        "cd4_date": lp_date,
                        "serum_crag_value": POS,
                        "serum_crag_date": lp_date,
                        "lp_done": YES,
                        "lp_date": lp_date,
                        "lp_declined": NOT_APPLICABLE,
                        "cm_in_csf": PENDING,
                        "cm_in_csf_date": lp_date + relativedelta(days=days),
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_cm_in_csf_date_before_report_date_raises(self):
        for days in [1, 2, 10]:
            with self.subTest(days_before=days):
                cleaned_data = self.get_cleaned_data()
                lp_date = cleaned_data.get("report_datetime").date() - relativedelta(days=10)
                cleaned_data.update(
                    {
                        "cd4_value": self.ELIGIBLE_CD4_VALUE,
                        "cd4_date": lp_date,
                        "serum_crag_value": POS,
                        "serum_crag_date": lp_date,
                        "lp_done": YES,
                        "lp_date": lp_date,
                        "lp_declined": NOT_APPLICABLE,
                        "cm_in_csf": PENDING,
                        "cm_in_csf_date": cleaned_data.get("report_datetime").date()
                        - relativedelta(days=days),
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("cm_in_csf_date", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Must be on or after report date/time. Got",
                    str(cm.exception.error_dict.get("cm_in_csf_date")),
                )

    def test_cm_in_csf_date_on_after_report_date_ok(self):
        for days in [0, 1, 2, 10]:
            with self.subTest(days_after=days):
                cleaned_data = self.get_cleaned_data()
                lp_date = cleaned_data.get("report_datetime").date()
                cleaned_data.update(
                    {
                        "cd4_value": self.ELIGIBLE_CD4_VALUE,
                        "cd4_date": lp_date,
                        "serum_crag_value": POS,
                        "serum_crag_date": lp_date,
                        "lp_done": YES,
                        "lp_date": lp_date,
                        "lp_declined": NOT_APPLICABLE,
                        "cm_in_csf": PENDING,
                        "cm_in_csf_date": cleaned_data.get("report_datetime").date()
                        + relativedelta(days=days),
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_gender_male_no_pregnancy_answers_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "gender": MALE,
                "pregnant": NOT_APPLICABLE,
                "preg_test_date": None,
                "breast_feeding": NOT_APPLICABLE,
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_gender_male_and_pregnant_not_not_applicable_raises(self):
        for answ in [YES, NO, NOT_EVALUATED]:
            with self.subTest(pregnant=answ):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "gender": MALE,
                        "pregnant": answ,
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("pregnant", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Subject is male",
                    str(cm.exception.error_dict.get("pregnant")),
                )

    def test_gender_male_and_pregnant_not_applicable_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "gender": MALE,
                "pregnant": NOT_APPLICABLE,
                "breast_feeding": NOT_APPLICABLE,
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_gender_male_and_preg_test_date_raises(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "gender": MALE,
                "preg_test_date": get_utcnow_as_date(),
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("preg_test_date", cm.exception.error_dict)
        self.assertIn(
            "Invalid. Subject is male",
            str(cm.exception.error_dict.get("preg_test_date")),
        )

    def test_gender_male_and_breast_feeding_raises(self):
        for answ in [YES, NO, NOT_EVALUATED]:
            with self.subTest(breast_feeding=answ):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "gender": MALE,
                        "pregnant": NOT_APPLICABLE,
                        "preg_test_date": None,
                        "breast_feeding": answ,
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("breast_feeding", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable.",
                    str(cm.exception.error_dict.get("breast_feeding")),
                )

    def test_unsuitable_reason_applicable_if_unsuitable_for_study_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "unsuitable_for_study": YES,
                "unsuitable_reason": NOT_APPLICABLE,
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("unsuitable_reason", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("unsuitable_reason")),
        )

        cleaned_data.update({"unsuitable_reason": DECEASED})
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_unsuitable_reason_not_applicable_if_unsuitable_for_study_not_yes(self):
        for answ in [NO, NOT_EVALUATED]:
            with self.subTest(answ=answ):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "unsuitable_for_study": answ,
                        "unsuitable_reason": UNABLE_TO_CONTACT,
                    }
                )
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("unsuitable_reason", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable.",
                    str(cm.exception.error_dict.get("unsuitable_reason")),
                )

                cleaned_data.update({"unsuitable_reason": NOT_APPLICABLE})
                form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_unsuitable_reason_other_not_required_if_unsuitable_reason_is_not_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "unsuitable_for_study": YES,
                "unsuitable_reason": UNABLE_TO_CONTACT,
                "unsuitable_reason_other": "some other reason",
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("unsuitable_reason_other", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("unsuitable_reason_other")),
        )

        cleaned_data.update({"unsuitable_reason_other": ""})
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_unsuitable_reason_other_required_if_unsuitable_reason_is_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "unsuitable_for_study": YES,
                "unsuitable_reason": OTHER,
                "unsuitable_reason_other": "",
                "unsuitable_agreed": YES,
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("unsuitable_reason_other", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("unsuitable_reason_other")),
        )

        cleaned_data.update({"unsuitable_reason_other": "Some other reason"})
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_unsuitable_agreed_applicable_if_unsuitable_for_study_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "unsuitable_for_study": YES,
                "unsuitable_reason": OTHER,
                "unsuitable_reason_other": "Some reason",
                "unsuitable_agreed": NOT_APPLICABLE,
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("unsuitable_agreed", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("unsuitable_agreed")),
        )

    def test_unsuitable_agreed_not_applicable_if_unsuitable_for_study_not_other(self):
        for unsuitable_answ in [YES, NO, NOT_EVALUATED]:
            for agreed_answ in [YES, NO]:
                with self.subTest(
                    unsuitable_for_study=unsuitable_answ, unsuitable_agreed=agreed_answ
                ):
                    cleaned_data = self.get_cleaned_data()
                    cleaned_data.update(
                        {
                            "unsuitable_for_study": unsuitable_answ,
                            "unsuitable_reason": (
                                DECEASED if unsuitable_answ == YES else NOT_APPLICABLE
                            ),
                            "unsuitable_agreed": agreed_answ,
                        }
                    )
                    form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn("unsuitable_agreed", cm.exception.error_dict)
                    self.assertIn(
                        "This field is not applicable.",
                        str(cm.exception.error_dict.get("unsuitable_agreed")),
                    )

    def test_unsuitable_agreed_not_yes_raises_if_unsuitable_for_study_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "unsuitable_for_study": YES,
                "unsuitable_reason": OTHER,
                "unsuitable_reason_other": "some other reason",
                "unsuitable_agreed": NO,
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("unsuitable_agreed", cm.exception.error_dict)
        self.assertIn(
            (
                "The study coordinator MUST agree with your assessment. "
                "Please discuss before continuing."
            ),
            str(cm.exception.error_dict.get("unsuitable_agreed")),
        )

    def test_unsuitable_agreed_yes_with_unsuitable_reason_other_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "unsuitable_for_study": YES,
                "unsuitable_reason": OTHER,
                "unsuitable_reason_other": "some other reason",
                "unsuitable_agreed": YES,
            }
        )
        form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_key_dates_after_report_datetime_raises(self):
        for date_field in [
            "hiv_confirmed_date",
            "cd4_date",
            "serum_crag_date",
            "lp_date",
            "preg_test_date",
        ]:
            for days_after in [1, 2, 10]:
                with self.subTest(date_field=date_field, days_after=days_after):
                    cleaned_data = self.get_cleaned_data()
                    report_datetime = cleaned_data["report_datetime"]
                    cleaned_data.update(
                        {date_field: report_datetime.date() + relativedelta(days=days_after)}
                    )
                    form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn(date_field, cm.exception.error_dict)
                    self.assertIn(
                        "Invalid. Must be on or before report date/time. Got ",
                        str(cm.exception.error_dict.get(date_field)),
                    )

    def test_key_dates_on_or_before_report_datetime_ok(self):
        for date_field in [
            "hiv_confirmed_date",
            "cd4_date",
            "serum_crag_date",
            "lp_date",
            "preg_test_date",
        ]:
            for days_before in [0, 1]:
                with self.subTest(date_field=date_field, days_before=days_before):
                    cleaned_data = self.get_cleaned_data()
                    report_datetime = cleaned_data["report_datetime"]
                    date_value = report_datetime.date() - relativedelta(days=days_before)
                    if date_field not in ["serum_crag_date", "lp_date"]:
                        cleaned_data.update({date_field: date_value})
                    else:
                        cleaned_data.update(
                            {
                                "serum_crag_date": date_value,
                                "lp_date": date_value - relativedelta(days=1),
                            }
                        )
                    form_validator = SubjectScreeningFormValidator(cleaned_data=cleaned_data)
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")
