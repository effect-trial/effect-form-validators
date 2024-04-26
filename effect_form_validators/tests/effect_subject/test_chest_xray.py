from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.test import TestCase
from django_mock_queries.query import MockModel, MockSet
from edc_constants.constants import NO, NORMAL, OTHER, YES
from edc_form_validators.tests.mixins import FormValidatorTestMixin
from edc_utils import get_utcnow

from effect_form_validators.effect_subject import ChestXrayFormValidator as Base

from ..mixins import TestCaseMixin


class ChestXrayMockModel(MockModel):
    @classmethod
    def related_visit_model_attr(cls) -> str:
        return "subject_visit"


class ChestXrayFormValidator(FormValidatorTestMixin, Base):
    @property
    def consent_datetime(self) -> datetime:
        return get_utcnow() - relativedelta(years=1)

    @property
    def previous_chest_xray_date(self) -> datetime.date:
        return (self.consent_datetime - relativedelta(months=1)).date()

    def get_consent_datetime_or_raise(self, **kwargs) -> datetime:
        return self.consent_datetime


class TestChestXrayFormValidation(TestCaseMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        # signs_and_symptoms
        self.signs_and_symptoms = MockModel(
            mock_name="SignsAndSymptoms",
            subject_visit=self.subject_visit,
            report_datetime=self.subject_visit.report_datetime,
            xray_performed=YES,
        )
        self.xray_result_other = MockModel(
            mock_name="XrayResults", name=OTHER, display_name=OTHER
        )
        self.xray_result_normal = MockModel(
            mock_name="XrayResults", name=NORMAL, display_name=NORMAL
        )
        # set for reverse lookup
        self.subject_visit.signsandsymptoms = self.signs_and_symptoms

    def get_cleaned_data(self, **kwargs) -> dict:
        cleaned_data = super().get_cleaned_data(**kwargs)
        cleaned_data.update(
            chest_xray=YES,
            chest_xray_date=self.subject_visit.report_datetime.date(),
            chest_xray_results=MockSet(self.xray_result_normal),
            chest_xray_results_other=None,
        )
        return cleaned_data

    def test_chest_xray_ok(self):
        self.subject_visit.signsandsymptoms.xray_performed = YES
        form_validator = ChestXrayFormValidator(
            cleaned_data=self.get_cleaned_data(), model=ChestXrayMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_no_chest_xray_raises(self):
        self.subject_visit.signsandsymptoms.xray_performed = NO
        form_validator = ChestXrayFormValidator(
            cleaned_data=self.get_cleaned_data(), model=ChestXrayMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("chest_xray", cm.exception.error_dict)

    def test_no_chest_xray_ok(self):
        cleaned_data = self.get_cleaned_data()
        self.subject_visit.signsandsymptoms.xray_performed = NO
        cleaned_data.update(
            chest_xray=NO,
            chest_xray_date=None,
            chest_xray_results=None,
            chest_xray_results_other=None,
        )
        form_validator = ChestXrayFormValidator(
            cleaned_data=cleaned_data, model=ChestXrayMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_chest_xray_other_field_not_expected_raises(self):
        cleaned_data = self.get_cleaned_data()
        self.subject_visit.signsandsymptoms.xray_performed = YES
        cleaned_data.update(
            chest_xray=YES,
            chest_xray_date=self.subject_visit.report_datetime.date(),
            chest_xray_results=MockSet(self.xray_result_normal),
            chest_xray_results_other="blah",
        )
        form_validator = ChestXrayFormValidator(
            cleaned_data=cleaned_data, model=ChestXrayMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("chest_xray_results_other", cm.exception.error_dict)

    def test_chest_xray_other_field_expected_raises(self):
        cleaned_data = self.get_cleaned_data()
        self.subject_visit.signsandsymptoms.xray_performed = YES
        cleaned_data.update(
            chest_xray=YES,
            chest_xray_date=self.subject_visit.report_datetime.date(),
            chest_xray_results=MockSet(self.xray_result_other),
            chest_xray_results_other=None,
        )
        form_validator = ChestXrayFormValidator(
            cleaned_data=cleaned_data, model=ChestXrayMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("chest_xray_results_other", cm.exception.error_dict)

    def test_chest_xray_other_field_expected_ok(self):
        cleaned_data = self.get_cleaned_data()
        self.subject_visit.signsandsymptoms.xray_performed = YES
        cleaned_data.update(
            chest_xray=YES,
            chest_xray_date=self.subject_visit.report_datetime.date(),
            chest_xray_results=MockSet(self.xray_result_other),
            chest_xray_results_other="blah",
        )
        form_validator = ChestXrayFormValidator(
            cleaned_data=cleaned_data, model=ChestXrayMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_chest_xray_expects_date_raises(self):
        cleaned_data = self.get_cleaned_data()
        self.subject_visit.signsandsymptoms.xray_performed = YES
        cleaned_data.update(
            chest_xray=YES,
            chest_xray_date=None,
            chest_xray_results=None,
            chest_xray_results_other=None,
        )
        form_validator = ChestXrayFormValidator(
            cleaned_data=cleaned_data, model=ChestXrayMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("chest_xray_date", cm.exception.error_dict)

    def test_chest_xray_expects_chest_xray_results_raises(self):
        cleaned_data = self.get_cleaned_data()
        self.subject_visit.signsandsymptoms.xray_performed = YES
        cleaned_data.update(
            chest_xray=YES,
            chest_xray_date=self.subject_visit.report_datetime.date(),
            chest_xray_results=None,
            chest_xray_results_other=None,
        )
        form_validator = ChestXrayFormValidator(
            cleaned_data=cleaned_data, model=ChestXrayMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("chest_xray_results", cm.exception.error_dict)

    def test_chest_xray_performed_with_chest_xray_no_raises(self):
        cleaned_data = self.get_cleaned_data()
        self.subject_visit.signsandsymptoms.xray_performed = YES
        cleaned_data.update(
            chest_xray=NO,
            chest_xray_date=None,
            chest_xray_results=None,
            chest_xray_results_other=None,
        )
        form_validator = ChestXrayFormValidator(
            cleaned_data=cleaned_data, model=ChestXrayMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("chest_xray", cm.exception.error_dict)
        self.assertIn(
            "Invalid. X-ray performed. Expected YES.",
            str(cm.exception.error_dict.get("chest_xray")),
        )

    def test_chest_xray_not_performed_with_chest_xray_yes_raises(self):
        cleaned_data = self.get_cleaned_data()
        self.subject_visit.signsandsymptoms.xray_performed = NO
        cleaned_data.update(
            chest_xray=YES,
            chest_xray_date=self.subject_visit.report_datetime.date(),
            chest_xray_results=None,
            chest_xray_results_other=None,
        )
        form_validator = ChestXrayFormValidator(
            cleaned_data=cleaned_data, model=ChestXrayMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("chest_xray", cm.exception.error_dict)
        self.assertIn(
            "Invalid. X-ray not performed. Expected NO.",
            str(cm.exception.error_dict.get("chest_xray")),
        )

    def test_no_chest_xray_with_date_raises(self):
        cleaned_data = self.get_cleaned_data()
        self.subject_visit.signsandsymptoms.xray_performed = NO
        cleaned_data.update(
            chest_xray=NO,
            chest_xray_date=self.subject_visit.report_datetime.date(),
            chest_xray_results=None,
            chest_xray_results_other=None,
        )
        form_validator = ChestXrayFormValidator(
            cleaned_data=cleaned_data, model=ChestXrayMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("chest_xray_date", cm.exception.error_dict)

    def test_cannot_have_other_results_with_normal(self):
        xray_results = MockSet(self.xray_result_normal, self.xray_result_other)
        cleaned_data = self.get_cleaned_data()
        self.subject_visit.signsandsymptoms.xray_performed = YES
        cleaned_data.update(
            chest_xray=YES,
            chest_xray_date=self.subject_visit.report_datetime.date(),
            chest_xray_results=xray_results,
            chest_xray_results_other=None,
        )
        form_validator = ChestXrayFormValidator(
            cleaned_data=cleaned_data, model=ChestXrayMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("chest_xray_results", cm.exception.error_dict)
        self.assertIn(
            "Invalid combination",
            str(cm.exception.error_dict.get("chest_xray_results")),
        )

    def test_chest_xray_date_gt_7_days_before_consent_date_raises(self):
        cleaned_data = self.get_cleaned_data()
        self.subject_visit.signsandsymptoms.xray_performed = YES
        for days_before_consent in [8, 9, 14, 21]:
            with self.subTest(days_before_consent=days_before_consent):
                cleaned_data.update(
                    chest_xray=YES,
                    chest_xray_date=(
                        self.consent_datetime - relativedelta(days=days_before_consent)
                    ).date(),
                    chest_xray_results=None,
                    chest_xray_results_other=None,
                )
                form_validator = ChestXrayFormValidator(
                    cleaned_data=cleaned_data, model=ChestXrayMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("chest_xray_date", cm.exception.error_dict)
                self.assertIn(
                    (
                        "Invalid. Expected date during this episode. "
                        "Cannot be >7 days before consent date"
                    ),
                    str(cm.exception.error_dict.get("chest_xray_date")),
                )

    def test_chest_xray_date_lte_7_days_before_consent_date_ok(self):
        cleaned_data = self.get_cleaned_data()
        self.subject_visit.signsandsymptoms.xray_performed = YES
        for days_before_consent in [0, 1, 7]:
            with self.subTest(days_before_consent=days_before_consent):
                report_datetime = self.consent_datetime - relativedelta(
                    days=days_before_consent
                )
                cleaned_data.update(
                    report_datetime=report_datetime,
                    chest_xray=YES,
                    chest_xray_date=report_datetime.date(),
                    chest_xray_results=MockSet(self.xray_result_normal),
                    chest_xray_results_other=None,
                )
                form_validator = ChestXrayFormValidator(
                    cleaned_data=cleaned_data, model=ChestXrayMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_chest_xray_date_on_or_after_consent_date_ok(self):
        cleaned_data = self.get_cleaned_data()
        self.subject_visit.signsandsymptoms.xray_performed = YES
        for days_after_consent in [0, 1, 7, 21]:
            with self.subTest(days_after_consent=days_after_consent):
                report_datetime = self.consent_datetime + relativedelta(
                    days=days_after_consent
                )
                cleaned_data.update(
                    report_datetime=report_datetime,
                    chest_xray=YES,
                    chest_xray_date=report_datetime.date(),
                    chest_xray_results=MockSet(self.xray_result_normal),
                    chest_xray_results_other=None,
                )
                form_validator = ChestXrayFormValidator(
                    cleaned_data=cleaned_data, model=ChestXrayMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")
