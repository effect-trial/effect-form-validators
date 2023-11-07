from dateutil.relativedelta import relativedelta
from django import forms
from django.test import TestCase
from django_mock_queries.query import MockModel, MockSet
from edc_constants.choices import DATE_ESTIMATED_NA
from edc_constants.constants import (
    NO,
    NOT_APPLICABLE,
    NOT_ESTIMATED,
    OTHER,
    UNKNOWN,
    YES,
)
from edc_form_validators import FormValidatorTestCaseMixin
from edc_form_validators.tests.mixins import FormValidatorTestMixin
from edc_utils import get_utcnow

from effect_form_validators.effect_ae import DeathReportFormValidator as Base

from ..mixins import TestCaseMixin


class DeathReportFormValidator(FormValidatorTestMixin, Base):
    @property
    def cause_of_death_model_cls(self):
        return MockModel(
            mock_name="CauseOfDeath",
            objects=MockSet(MockModel(name=OTHER), MockModel(name=UNKNOWN)),
        )


class TestDeathReportFormValidation(FormValidatorTestCaseMixin, TestCaseMixin, TestCase):
    form_validator_cls = DeathReportFormValidator

    def setUp(self) -> None:
        super().setUp()

    def get_cleaned_data(self, **kwargs) -> dict:
        cleaned_data = super().get_cleaned_data(**kwargs)
        cleaned_data.update(
            {
                "report_datetime": get_utcnow(),
                "death_datetime": get_utcnow() - relativedelta(days=1, hours=6),
                "death_as_inpatient": NO,
                "hospitalization_date": None,
                "hospitalization_date_estimated": NOT_APPLICABLE,
                "clinical_notes_available": NOT_APPLICABLE,
                "cm_sx": NOT_APPLICABLE,
                "speak_nok": NO,
                "date_first_unwell": None,
                "date_first_unwell_estimated": NOT_APPLICABLE,
                "headache": NOT_APPLICABLE,
                "drowsy_confused_altered_behaviour": NOT_APPLICABLE,
                "seizures": NOT_APPLICABLE,
                "blurred_vision": NOT_APPLICABLE,
                "nok_narrative": NOT_APPLICABLE,
                "cause_of_death": UNKNOWN,
                "cause_of_death_other": "",
                "narrative": "Details of death",
            }
        )
        return cleaned_data

    def test_cleaned_data_ok(self):
        cleaned_data = self.get_cleaned_data()
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_death_datetime_after_report_datetime_raises(self):
        for days_after in [1, 3, 14]:
            with self.subTest(days_after=days_after):
                cleaned_data = self.get_cleaned_data()
                report_datetime = get_utcnow()
                cleaned_data.update(
                    {
                        "report_datetime": get_utcnow(),
                        "death_datetime": report_datetime + relativedelta(days=days_after),
                    }
                )
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("report_datetime", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Expected a date on or after",
                    str(cm.exception.error_dict.get("report_datetime")),
                )
                self.assertIn(
                    "(on or after date of death)",
                    str(cm.exception.error_dict.get("report_datetime")),
                )

    def test_death_datetime_on_or_before_report_datetime_datetime_ok(self):
        for days_before in [0, 1, 2, 14]:
            with self.subTest(days_before=days_before):
                cleaned_data = self.get_cleaned_data()
                report_datetime = get_utcnow()
                cleaned_data.update(
                    {
                        "report_datetime": report_datetime,
                        "death_datetime": report_datetime - relativedelta(days=days_before),
                    }
                )
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except forms.ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_hospitalization_date_required_if_death_as_inpatient_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update({"death_as_inpatient": YES})
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("hospitalization_date", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("hospitalization_date")),
        )

        cleaned_data.update(
            {
                "hospitalization_date": (
                    cleaned_data.get("death_datetime").date() - relativedelta(days=3)
                ),
                "hospitalization_date_estimated": NO,
                "clinical_notes_available": NO,
                "cm_sx": NOT_APPLICABLE,
            }
        )
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_hospitalization_date_not_required_if_death_as_inpatient_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "death_as_inpatient": NO,
                "hospitalization_date": (
                    cleaned_data.get("death_datetime").date() - relativedelta(days=3)
                ),
            }
        )
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("hospitalization_date", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("hospitalization_date")),
        )

        cleaned_data.update({"hospitalization_date": None})
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_hospitalization_date_after_death_date_raises(self):
        for days_after in [1, 3, 10]:
            with self.subTest(days_after=days_after):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "death_as_inpatient": YES,
                        "hospitalization_date": (
                            cleaned_data.get("death_datetime").date()
                            + relativedelta(days=days_after)
                        ),
                    }
                )
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("hospitalization_date", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Expected a date on or before",
                    str(cm.exception.error_dict.get("hospitalization_date")),
                )
                self.assertIn(
                    "(on or before date of death)",
                    str(cm.exception.error_dict.get("hospitalization_date")),
                )

    def test_hospitalization_date_on_or_before_death_date_ok(self):
        for days_before in [0, 1, 3, 10]:
            with self.subTest(days_before=days_before):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "death_as_inpatient": YES,
                        "hospitalization_date": (
                            cleaned_data.get("death_datetime").date()
                            - relativedelta(days=days_before)
                        ),
                        "hospitalization_date_estimated": NO,
                        "clinical_notes_available": NO,
                        "cm_sx": NOT_APPLICABLE,
                    }
                )
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except forms.ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_hospitalisation_date_estimated_applicable_if_death_as_inpatient_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "death_as_inpatient": YES,
                "hospitalization_date": (
                    cleaned_data.get("death_datetime").date() - relativedelta(days=1)
                ),
                "hospitalization_date_estimated": NOT_APPLICABLE,
            }
        )
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("hospitalization_date_estimated", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("hospitalization_date_estimated")),
        )

        for answ in [c[0] for c in DATE_ESTIMATED_NA if c[0] != NOT_APPLICABLE]:
            with self.subTest(answ=answ):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "death_as_inpatient": YES,
                        "hospitalization_date": (
                            cleaned_data.get("death_datetime").date() - relativedelta(days=1)
                        ),
                        "hospitalization_date_estimated": answ,
                        "clinical_notes_available": NO,
                        "cm_sx": NOT_APPLICABLE,
                    }
                )
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except forms.ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_hospitalisation_date_estimated_not_applicable_if_death_as_inpatient_no(self):
        cleaned_data = self.get_cleaned_data()
        for answ in [c[0] for c in DATE_ESTIMATED_NA if c[0] != NOT_APPLICABLE]:
            with self.subTest(answ=answ):
                cleaned_data.update(
                    {
                        "death_as_inpatient": NO,
                        "hospitalization_date": None,
                        "hospitalization_date_estimated": answ,
                    }
                )
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("hospitalization_date_estimated", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable.",
                    str(cm.exception.error_dict.get("hospitalization_date_estimated")),
                )

        cleaned_data.update(
            {
                "death_as_inpatient": NO,
                "hospitalization_date": None,
                "hospitalization_date_estimated": NOT_APPLICABLE,
            }
        )
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_clinical_notes_available_applicable_if_death_as_inpatient_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "death_as_inpatient": YES,
                "hospitalization_date": (
                    cleaned_data.get("death_datetime").date() - relativedelta(days=1)
                ),
                "hospitalization_date_estimated": NOT_ESTIMATED,
                "clinical_notes_available": NOT_APPLICABLE,
                "cm_sx": NOT_APPLICABLE,
            }
        )
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("clinical_notes_available", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("clinical_notes_available")),
        )

        for answ in [YES, NO]:
            with self.subTest(answ=answ):
                cleaned_data.update(
                    {
                        "clinical_notes_available": answ,
                        "cm_sx": NO if answ == YES else NOT_APPLICABLE,
                    }
                )
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except forms.ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_clinical_notes_available_not_applicable_if_death_as_inpatient_no(self):
        cleaned_data = self.get_cleaned_data()
        for answ in [YES, NO]:
            with self.subTest(answ=answ):
                cleaned_data.update(
                    {
                        "death_as_inpatient": NO,
                        "clinical_notes_available": answ,
                    }
                )
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("clinical_notes_available", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable.",
                    str(cm.exception.error_dict.get("clinical_notes_available")),
                )

        cleaned_data.update({"clinical_notes_available": NOT_APPLICABLE})
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_cm_sx_applicable_if_clinical_notes_available_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "death_as_inpatient": YES,
                "hospitalization_date": (
                    cleaned_data.get("death_datetime").date() - relativedelta(days=1)
                ),
                "hospitalization_date_estimated": NOT_ESTIMATED,
                "clinical_notes_available": YES,
                "cm_sx": NOT_APPLICABLE,
            }
        )
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("cm_sx", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("cm_sx")),
        )

        for answ in [YES, NO]:
            with self.subTest(answ=answ):
                cleaned_data.update({"cm_sx": answ})
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except forms.ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_cm_sx_not_applicable_if_clinical_notes_available_no(self):
        cleaned_data = self.get_cleaned_data()
        for answ in [YES, NO]:
            with self.subTest(answ=answ):
                cleaned_data.update(
                    {
                        "death_as_inpatient": YES,
                        "hospitalization_date": (
                            cleaned_data.get("death_datetime").date() - relativedelta(days=1)
                        ),
                        "hospitalization_date_estimated": NOT_ESTIMATED,
                        "clinical_notes_available": NO,
                        "cm_sx": answ,
                    }
                )
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("cm_sx", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable.",
                    str(cm.exception.error_dict.get("cm_sx")),
                )

        cleaned_data.update({"cm_sx": NOT_APPLICABLE})
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_date_first_unwell_required_if_speak_nok_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update({"speak_nok": YES})
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("date_first_unwell", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("date_first_unwell")),
        )

        cleaned_data.update(
            {
                "date_first_unwell": (
                    cleaned_data.get("death_datetime").date() - relativedelta(days=3)
                ),
                "date_first_unwell_estimated": NO,
                "headache": NO,
                "drowsy_confused_altered_behaviour": NO,
                "seizures": NO,
                "blurred_vision": NO,
                "nok_narrative": "Narrative from nok...",
            }
        )
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_date_first_unwell_not_required_if_speak_nok_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "speak_nok": NO,
                "date_first_unwell": (
                    cleaned_data.get("death_datetime").date() - relativedelta(days=3)
                ),
            }
        )
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("date_first_unwell", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("date_first_unwell")),
        )

        cleaned_data.update({"date_first_unwell": None})
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_date_first_unwell_after_death_date_raises(self):
        for days_after in [1, 3, 10]:
            with self.subTest(days_after=days_after):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "speak_nok": YES,
                        "date_first_unwell": (
                            cleaned_data.get("death_datetime").date()
                            + relativedelta(days=days_after)
                        ),
                    }
                )
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("date_first_unwell", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Expected a date on or before",
                    str(cm.exception.error_dict.get("date_first_unwell")),
                )
                self.assertIn(
                    "(on or before date of death)",
                    str(cm.exception.error_dict.get("date_first_unwell")),
                )

    def test_date_first_unwell_on_or_before_death_date_ok(self):
        for days_before in [0, 1, 3, 10]:
            with self.subTest(days_before=days_before):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "speak_nok": YES,
                        "date_first_unwell": (
                            cleaned_data.get("death_datetime").date()
                            - relativedelta(days=days_before)
                        ),
                        "date_first_unwell_estimated": NO,
                        "headache": NO,
                        "drowsy_confused_altered_behaviour": NO,
                        "seizures": NO,
                        "blurred_vision": NO,
                        "nok_narrative": "Narrative from nok...",
                    }
                )
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except forms.ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_date_first_unwell_after_hospitalization_date_raises(self):
        cleaned_data = self.get_cleaned_data()
        hospitalization_date = cleaned_data.get("death_datetime").date() - relativedelta(
            days=7
        )
        for days_after in [1, 3, 7]:
            with self.subTest(days_after=days_after):
                cleaned_data.update(
                    {
                        "death_as_inpatient": YES,
                        "hospitalization_date": hospitalization_date,
                        "hospitalization_date_estimated": NOT_ESTIMATED,
                        "clinical_notes_available": NO,
                        "speak_nok": YES,
                        "date_first_unwell": (
                            hospitalization_date + relativedelta(days=days_after)
                        ),
                    }
                )
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("date_first_unwell", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. Expected a date on or before",
                    str(cm.exception.error_dict.get("date_first_unwell")),
                )
                self.assertIn(
                    "(on or before date of hospitalization)",
                    str(cm.exception.error_dict.get("date_first_unwell")),
                )

    def test_date_first_unwell_on_or_before_hospitalization_date_ok(self):
        cleaned_data = self.get_cleaned_data()
        hospitalization_date = cleaned_data.get("death_datetime").date() - relativedelta(
            days=7
        )
        for days_before in [0, 1, 3, 10]:
            with self.subTest(days_before=days_before):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "death_as_inpatient": YES,
                        "hospitalization_date": hospitalization_date,
                        "hospitalization_date_estimated": NOT_ESTIMATED,
                        "clinical_notes_available": NO,
                        "speak_nok": YES,
                        "date_first_unwell": (
                            hospitalization_date - relativedelta(days=days_before)
                        ),
                        "date_first_unwell_estimated": NO,
                        "headache": NO,
                        "drowsy_confused_altered_behaviour": NO,
                        "seizures": NO,
                        "blurred_vision": NO,
                        "nok_narrative": "Narrative from nok...",
                    }
                )
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except forms.ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_nok_questions_not_applicable_if_speak_nok_no(self):
        for nok_question in [
            "headache",
            "drowsy_confused_altered_behaviour",
            "seizures",
            "blurred_vision",
        ]:
            for answ in [YES, NO, UNKNOWN]:
                with self.subTest(nok_question=nok_question, answ=answ):
                    cleaned_data = self.get_cleaned_data()
                    cleaned_data.update(
                        {
                            "speak_nok": NO,
                            nok_question: answ,
                        }
                    )
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(forms.ValidationError) as cm:
                    form_validator.validate()
                self.assertIn(nok_question, cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable.",
                    str(cm.exception.error_dict.get(nok_question)),
                )

                cleaned_data.update({nok_question: NOT_APPLICABLE})
                form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except forms.ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_nok_questions_applicable_if_speak_nok_yes(self):
        for nok_question in [
            "headache",
            "drowsy_confused_altered_behaviour",
            "seizures",
            "blurred_vision",
        ]:
            for answ in [YES, NO, UNKNOWN]:
                with self.subTest(nok_question=nok_question, answ=answ):
                    cleaned_data = self.get_cleaned_data()
                    cleaned_data.update(
                        {
                            "speak_nok": YES,
                            "date_first_unwell": (
                                cleaned_data.get("death_datetime").date()
                                - relativedelta(days=3)
                            ),
                            "date_first_unwell_estimated": NO,
                            "headache": UNKNOWN,
                            "drowsy_confused_altered_behaviour": UNKNOWN,
                            "seizures": UNKNOWN,
                            "blurred_vision": UNKNOWN,
                            "nok_narrative": "Narrative from nok...",
                        }
                    )
                    cleaned_data.update({nok_question: NOT_APPLICABLE})
                    form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                    with self.assertRaises(forms.ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn(nok_question, cm.exception.error_dict)
                    self.assertIn(
                        "This field is applicable.",
                        str(cm.exception.error_dict.get(nok_question)),
                    )

                    cleaned_data.update({nok_question: answ})
                    form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
                    try:
                        form_validator.validate()
                    except forms.ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_nok_narrative_not_required_if_speak_nok_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "speak_nok": NO,
                "nok_narrative": "Narrative from nok...",
            }
        )
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("nok_narrative", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("nok_narrative")),
        )

        cleaned_data.update({"nok_narrative": ""})
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_nok_narrative_required_if_speak_nok_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "speak_nok": YES,
                "date_first_unwell": (
                    cleaned_data.get("death_datetime").date() - relativedelta(days=3)
                ),
                "date_first_unwell_estimated": NO,
                "headache": UNKNOWN,
                "drowsy_confused_altered_behaviour": UNKNOWN,
                "seizures": UNKNOWN,
                "blurred_vision": UNKNOWN,
                "nok_narrative": "",
            }
        )
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("nok_narrative", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("nok_narrative")),
        )

        cleaned_data.update(
            {
                "nok_narrative": "Narrative from nok...",
            }
        )
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_cause_of_death_other_required_if_cause_of_death_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "cause_of_death": OTHER,
                "cause_of_death_other": "",
            }
        )
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("cause_of_death_other", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("cause_of_death_other")),
        )

        cleaned_data.update({"cause_of_death_other": "Some other cause of death..."})
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_cause_of_death_other_not_required_if_cause_of_death_not_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "cause_of_death": UNKNOWN,
                "cause_of_death_other": "Some other cause of death",
            }
        )
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("cause_of_death_other", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("cause_of_death_other")),
        )

        cleaned_data.update({"cause_of_death_other": ""})
        form_validator = DeathReportFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")
