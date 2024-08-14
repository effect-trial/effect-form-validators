from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.test import TestCase
from django_mock_queries.query import MockModel
from edc_constants.constants import NEW
from edc_form_validators.tests.mixins import FormValidatorTestMixin
from edc_utils import get_utcnow

from effect_form_validators.effect_reports import SerumCragDateNoteFormValidator as Base

from ..mixins import TestCaseMixin


class SerumCragDateNoteFormValidator(FormValidatorTestMixin, Base):
    pass


class TestSerumCragDateNoteFormValidator(TestCaseMixin, TestCase):
    def setUp(self) -> None:
        self.eligibility_datetime = get_utcnow() - relativedelta(years=1)

        subject_screening_patcher = patch(
            "effect_form_validators.effect_reports.serum_crag_date_note_form_validator"
            ".SerumCragDateNoteFormValidator.subject_screening"
        )
        self.addCleanup(subject_screening_patcher.stop)
        self.mock_subject_screening = subject_screening_patcher.start()
        self.mock_subject_screening.return_value = MockModel(mock_name="SubjectScreening")
        self.mock_subject_screening.eligibility_datetime.date.return_value = (
            self.eligibility_datetime.date()
        )

    def get_cleaned_data(self, **kwargs) -> dict:
        return dict(
            serum_crag_date=(self.eligibility_datetime - relativedelta(days=14)).date(),
            note="",
            status=NEW,
            report_model="effect_reports.consentedserumcragdate",
            subject_identifier="123-456-789",
            report_datetime=get_utcnow(),
        )

    def test_cleaned_data_ok(self):
        form_validator = SerumCragDateNoteFormValidator(cleaned_data=self.get_cleaned_data())
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_serum_crag_date_after_eligibility_raises(self):
        eligibility_date = self.mock_subject_screening.eligibility_datetime.date()
        for days_after in [1, 7, 14, 364, 365, 366]:
            with self.subTest(days_after=days_after):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    serum_crag_date=(eligibility_date + relativedelta(days=days_after)),
                )

                form_validator = SerumCragDateNoteFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("serum_crag_date", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Cannot be after date participant became eligible.",
                    cm.exception.message_dict.get("serum_crag_date"),
                )

    def test_serum_crag_date_gt_180_days_before_eligibility_raises(self):
        eligibility_date = self.mock_subject_screening.eligibility_datetime.date()
        for days_before in [181, 182, 200, 366]:
            with self.subTest(days_before=days_before):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    serum_crag_date=(eligibility_date - relativedelta(days=days_before))
                )

                form_validator = SerumCragDateNoteFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("serum_crag_date", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Cannot be more than 180 days before screening.",
                    cm.exception.message_dict.get("serum_crag_date"),
                )

    def test_serum_crag_date_lte_180_days_before_eligibility_ok(self):
        eligibility_date = self.mock_subject_screening.eligibility_datetime.date()
        for days_before in [0, 1, 7, 14, 20, 21, 179, 180]:
            with self.subTest(days_before=days_before):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    serum_crag_date=(eligibility_date - relativedelta(days=days_before))
                )

                form_validator = SerumCragDateNoteFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_serum_crag_date_gt_report_datetime_raises(self):
        eligibility_date = self.mock_subject_screening.eligibility_datetime.date()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            serum_crag_date=eligibility_date - relativedelta(days=7),
            report_datetime=eligibility_date - relativedelta(days=8),
        )

        form_validator = SerumCragDateNoteFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("serum_crag_date", cm.exception.error_dict)
        self.assertIn(
            "Invalid. Must be on or before report date/time.",
            str(cm.exception.message_dict.get("serum_crag_date")),
        )

    def test_serum_crag_date_lte_report_datetime_ok(self):
        eligibility_date = self.mock_subject_screening.eligibility_datetime.date()
        for days_before in [0, 1, 7, 14, 21, 180]:
            with self.subTest(days_before=days_before):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    serum_crag_date=(eligibility_date - relativedelta(days=days_before)),
                    report_datetime=eligibility_date,
                )

                form_validator = SerumCragDateNoteFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_no_serum_crag_date_and_no_note_raises(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            serum_crag_date=None,
            note="",
        )

        form_validator = SerumCragDateNoteFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()

        for field in ["serum_crag_date", "note"]:
            self.assertIn(field, cm.exception.error_dict)
            self.assertIn(
                "A confirmed serum/plasma CrAg date and/or note is required.",
                str(cm.exception.error_dict.get(field)),
            )

    def test_serum_crag_date_only_ok(self):
        eligibility_date = self.mock_subject_screening.eligibility_datetime.date()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            serum_crag_date=eligibility_date,
            note="",
        )

        form_validator = SerumCragDateNoteFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_note_only_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            serum_crag_date=None,
            note="Reason date is missing",
        )

        form_validator = SerumCragDateNoteFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_serum_crag_date_and_note_ok(self):
        eligibility_date = self.mock_subject_screening.eligibility_datetime.date()
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            serum_crag_date=eligibility_date,
            note="Details about the date",
            report_datetime=eligibility_date,
        )

        form_validator = SerumCragDateNoteFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")
