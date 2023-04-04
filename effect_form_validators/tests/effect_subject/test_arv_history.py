from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django_mock_queries.query import MockModel, MockSet
from edc_constants.choices import DATE_ESTIMATED_NA
from edc_constants.constants import DEFAULTED, NO, NOT_APPLICABLE, YES
from edc_form_validators.tests.mixins import FormValidatorTestMixin
from edc_utils import get_utcnow, get_utcnow_as_date

from effect_form_validators.effect_subject import ArvHistoryFormValidator as Base

from ...constants import ART_CONTINUED, ART_STOPPED
from ..mixins import TestCaseMixin


class ArvHistoryMockModel(MockModel):
    @classmethod
    def related_visit_model_attr(cls):
        return "subject_visit"


class ArvHistoryFormValidator(FormValidatorTestMixin, Base):
    @property
    def subject_screening(self):
        screening_date = get_utcnow_as_date() - relativedelta(years=1)
        return MockModel(
            mock_name="SubjectScreening",
            subject_identifier=self.subject_identifier,
            cd4_value=80,
            cd4_date=screening_date - relativedelta(days=7),
        )


class ArvHistoryWithoutSubjectScreeningMockFormValidator(FormValidatorTestMixin, Base):
    pass


class TestArvHistoryFormValidator(TestCaseMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.hiv_dx_date = self.screening_datetime.date() - relativedelta(days=30)

        self.arv_regimens_choice_na = MockModel(
            mock_name="ArvRegimens", name=NOT_APPLICABLE, display_name=NOT_APPLICABLE
        )

        self.arv_regimens_choice_abc_3tc_ftc = MockModel(
            mock_name="ArvRegimens", name="ABC_3TC/FTC", display_name="ABC_3TC/FTC"
        )

    def get_cleaned_data(self, **kwargs) -> dict:
        if "report_datetime" not in kwargs:
            kwargs["report_datetime"] = get_utcnow()
        cleaned_data = super().get_cleaned_data(**kwargs)
        cleaned_data.update(
            {
                # HIV Diagnosis
                "hiv_dx_date": self.hiv_dx_date,
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
                "cd4_value": 80,
                "cd4_date": self.screening_datetime.date() - relativedelta(days=7),
                "cd4_date_estimated": NO,
            }
        )
        return cleaned_data

    def test_cleaned_data_ok(self):
        cleaned_data = self.get_cleaned_data()
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_hiv_dx_date_before_screening_cd4_date_ok(self):
        class OverriddenArvHistoryFormValidator(FormValidatorTestMixin, Base):
            screening_cd4_date = self.hiv_dx_date + relativedelta(days=1)

            @property
            def subject_screening(self):
                return MockModel(
                    mock_name="SubjectScreening",
                    subject_identifier=self.subject_identifier,
                    cd4_date=self.screening_cd4_date,
                )

        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                # HIV Diagnosis
                "hiv_dx_date": self.hiv_dx_date,
                "hiv_dx_date_estimated": NO,
            }
        )
        form_validator = OverriddenArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_hiv_dx_date_matches_screening_cd4_date_ok(self):
        class OverriddenArvHistoryFormValidator(FormValidatorTestMixin, Base):
            screening_cd4_date = self.hiv_dx_date

            @property
            def subject_screening(self):
                return MockModel(
                    mock_name="SubjectScreening",
                    subject_identifier=self.subject_identifier,
                    cd4_date=self.screening_cd4_date,
                )

        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                # HIV Diagnosis
                "hiv_dx_date": self.hiv_dx_date,
                "hiv_dx_date_estimated": NO,
            }
        )
        form_validator = OverriddenArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_hiv_dx_date_after_screening_cd4_date_raises(self):
        screening_cd4_date = self.hiv_dx_date - relativedelta(days=1)

        class OverriddenArvHistoryFormValidator(FormValidatorTestMixin, Base):
            @property
            def subject_screening(self):
                return MockModel(
                    mock_name="SubjectScreening",
                    subject_identifier=self.subject_identifier,
                    cd4_date=screening_cd4_date,
                )

        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                # HIV Diagnosis
                "hiv_dx_date": self.hiv_dx_date,
                "hiv_dx_date_estimated": NO,
            }
        )
        form_validator = OverriddenArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("hiv_dx_date", cm.exception.error_dict)
        self.assertIn(
            f"Invalid. Cannot be after screening CD4 date ({screening_cd4_date}).",
            cm.exception.error_dict.get("hiv_dx_date")[0].message,
        )

    def test_has_defaulted_applicable_if_initial_art_date(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": NOT_APPLICABLE,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("has_defaulted", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable",
            str(cm.exception.error_dict.get("has_defaulted")),
        )

    def test_has_defaulted_not_applicable_if_initial_art_date_none(self):
        for has_defaulted in [YES, NO]:
            with self.subTest(has_defaulted=has_defaulted):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "on_art_at_crag": NO,
                        "ever_on_art": NO,
                        "initial_art_date": None,
                        "initial_art_date_estimated": NOT_APPLICABLE,
                        "has_defaulted": has_defaulted,
                    }
                )
                form_validator = ArvHistoryFormValidator(
                    cleaned_data=cleaned_data, model=ArvHistoryMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("has_defaulted", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable",
                    str(cm.exception.error_dict.get("has_defaulted")),
                )

    def test_has_defaulted_yes_if_initial_art_date_provided_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": YES,
                "defaulted_date": self.hiv_dx_date + relativedelta(days=14),
                "defaulted_date_estimated": "D",
                "is_adherent": DEFAULTED,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_has_defaulted_no_if_initial_art_date_provided_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": NO,
                "defaulted_date": None,
                "defaulted_date_estimated": NOT_APPLICABLE,
                "is_adherent": YES,
                "art_decision": ART_STOPPED,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_defaulted_date_required_if_has_defaulted_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": YES,
                "defaulted_date": None,
                "is_adherent": DEFAULTED,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("defaulted_date", cm.exception.error_dict)
        self.assertIn(
            "This field is required",
            str(cm.exception.error_dict.get("defaulted_date")),
        )

    def test_defaulted_date_not_required_if_has_defaulted_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": NO,
                "defaulted_date": self.hiv_dx_date + relativedelta(days=14),
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("defaulted_date", cm.exception.error_dict)
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("defaulted_date")),
        )

    def test_defaulted_date_with_has_defaulted_yes_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": YES,
                "defaulted_date": self.hiv_dx_date + relativedelta(days=14),
                "defaulted_date_estimated": "D",
                "is_adherent": DEFAULTED,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_defaulted_date_not_required_if_has_defaulted_not_applicable(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "has_defaulted": NOT_APPLICABLE,
                "defaulted_date": self.hiv_dx_date + relativedelta(days=14),
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("defaulted_date", cm.exception.error_dict)
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("defaulted_date")),
        )

    def test_defaulted_date_estimated_not_applicable_if_defaulted_date_none(self):
        for has_defaulted in [NO, NOT_APPLICABLE]:
            with self.subTest(has_defaulted=has_defaulted):
                cleaned_data = self.get_cleaned_data()
                if has_defaulted != NOT_APPLICABLE:
                    cleaned_data.update(
                        {
                            "ever_on_art": YES,
                            "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                            "initial_art_date_estimated": NO,
                            "initial_art_regimen": MockSet(
                                self.arv_regimens_choice_abc_3tc_ftc
                            ),
                            "has_switched_art_regimen": NO,
                        }
                    )
                cleaned_data.update(
                    {
                        "has_defaulted": has_defaulted,
                        "defaulted_date": None,
                        "defaulted_date_estimated": "D",
                    }
                )
                form_validator = ArvHistoryFormValidator(
                    cleaned_data=cleaned_data, model=ArvHistoryMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("defaulted_date_estimated", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable",
                    str(cm.exception.error_dict.get("defaulted_date_estimated")),
                )

    def test_defaulted_date_estimated_applicable_if_defaulted_date_provided(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": YES,
                "defaulted_date": self.hiv_dx_date + relativedelta(days=14),
                "defaulted_date_estimated": NOT_APPLICABLE,
                "is_adherent": DEFAULTED,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("defaulted_date_estimated", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable",
            str(cm.exception.error_dict.get("defaulted_date_estimated")),
        )

        for choice in [ch[0] for ch in DATE_ESTIMATED_NA if ch[0] != NOT_APPLICABLE]:
            with self.subTest(defaulted_date_estimated=choice):
                cleaned_data.update({"defaulted_date_estimated": choice})
                form_validator = ArvHistoryFormValidator(
                    cleaned_data=cleaned_data, model=ArvHistoryMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_is_adherent_not_applicable_if_has_defaulted_not_applicable(self):
        for is_adherent in [YES, NO, DEFAULTED]:
            with self.subTest(is_adherent=is_adherent):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "has_defaulted": NOT_APPLICABLE,
                        "is_adherent": is_adherent,
                    }
                )
                form_validator = ArvHistoryFormValidator(
                    cleaned_data=cleaned_data, model=ArvHistoryMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("is_adherent", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable",
                    str(cm.exception.error_dict.get("is_adherent")),
                )

    def test_is_adherent_applicable_if_has_defaulted_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": NO,
                "defaulted_date": None,
                "defaulted_date_estimated": NOT_APPLICABLE,
                "is_adherent": NOT_APPLICABLE,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("is_adherent", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable",
            str(cm.exception.error_dict.get("is_adherent")),
        )

    def test_is_adherent_defaulted_raises_if_has_defaulted_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": NO,
                "defaulted_date": None,
                "defaulted_date_estimated": NOT_APPLICABLE,
                "is_adherent": DEFAULTED,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("is_adherent", cm.exception.error_dict)
        self.assertIn(
            "Invalid. "
            "Participant not reported as defaulted from their current ART regimen.",
            str(cm.exception.error_dict.get("is_adherent")),
        )

    def test_is_adherent_not_defaulted_raises_if_has_defaulted_yes(self):
        for is_adherent in [YES, NO]:
            with self.subTest(is_adherent=is_adherent):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "ever_on_art": YES,
                        "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                        "initial_art_date_estimated": NO,
                        "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                        "has_switched_art_regimen": NO,
                        "has_defaulted": YES,
                        "defaulted_date": self.hiv_dx_date + relativedelta(days=14),
                        "defaulted_date_estimated": "D",
                        "is_adherent": is_adherent,
                    }
                )
                form_validator = ArvHistoryFormValidator(
                    cleaned_data=cleaned_data, model=ArvHistoryMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("is_adherent", cm.exception.error_dict)
                self.assertIn(
                    "Invalid. "
                    "Expected DEFAULTED. Participant reported as defaulted "
                    "from their current ART regimen.",
                    str(cm.exception.error_dict.get("is_adherent")),
                )

    def test_is_adherent_yes_if_has_defaulted_no_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": NO,
                "defaulted_date": None,
                "defaulted_date_estimated": NOT_APPLICABLE,
                "is_adherent": YES,
                "art_decision": ART_STOPPED,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_is_adherent_no_if_has_defaulted_no_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": NO,
                "defaulted_date": None,
                "defaulted_date_estimated": NOT_APPLICABLE,
                "is_adherent": NO,
                "art_doses_missed": 10,
                "art_decision": ART_STOPPED,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_is_adherent_defaulted_if_has_defaulted_yes_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": YES,
                "defaulted_date": self.hiv_dx_date + relativedelta(days=14),
                "defaulted_date_estimated": "D",
                "is_adherent": DEFAULTED,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_art_doses_missed_required_if_is_adherent_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": NO,
                "defaulted_date": None,
                "defaulted_date_estimated": NOT_APPLICABLE,
                "is_adherent": NO,
                "art_doses_missed": None,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("art_doses_missed", cm.exception.error_dict)
        self.assertIn(
            "This field is required",
            str(cm.exception.error_dict.get("art_doses_missed")),
        )

    def test_art_doses_missed_not_required_if_is_adherent_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": NO,
                "defaulted_date": None,
                "defaulted_date_estimated": NOT_APPLICABLE,
                "is_adherent": YES,
                "art_doses_missed": 3,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("art_doses_missed", cm.exception.error_dict)
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("art_doses_missed")),
        )

    def test_art_doses_missed_not_required_if_is_adherent_defaulted(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": YES,
                "defaulted_date": self.hiv_dx_date + relativedelta(days=14),
                "defaulted_date_estimated": "D",
                "is_adherent": DEFAULTED,
                "art_doses_missed": 3,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("art_doses_missed", cm.exception.error_dict)
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("art_doses_missed")),
        )

    def test_art_doses_missed_not_required_if_is_adherent_not_applicable(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "is_adherent": NOT_APPLICABLE,
                "art_doses_missed": 3,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("art_doses_missed", cm.exception.error_dict)
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("art_doses_missed")),
        )

    def test_art_doses_missed_ok_if_is_adherent_no(self):
        for art_doses_missed in [0, 1, 5, 10, 31]:
            with self.subTest(art_doses_missed=art_doses_missed):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "ever_on_art": YES,
                        "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                        "initial_art_date_estimated": NO,
                        "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                        "has_switched_art_regimen": NO,
                        "has_defaulted": NO,
                        "defaulted_date": None,
                        "defaulted_date_estimated": NOT_APPLICABLE,
                        "is_adherent": NO,
                        "art_doses_missed": art_doses_missed,
                        "art_decision": ART_CONTINUED,
                    }
                )
                form_validator = ArvHistoryFormValidator(
                    cleaned_data=cleaned_data, model=ArvHistoryMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_art_decision_not_applicable_if_has_defaulted_not_applicable(self):
        for art_decision in [ART_CONTINUED, ART_STOPPED]:
            with self.subTest(art_decision):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "has_defaulted": NOT_APPLICABLE,
                        "defaulted_date": None,
                        "defaulted_date_estimated": NOT_APPLICABLE,
                        "is_adherent": NOT_APPLICABLE,
                        "art_doses_missed": None,
                        "art_decision": art_decision,
                    }
                )
                form_validator = ArvHistoryFormValidator(
                    cleaned_data=cleaned_data, model=ArvHistoryMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("art_decision", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable",
                    str(cm.exception.error_dict.get("art_decision")),
                )

    def test_art_decision_not_applicable_if_has_defaulted_yes(self):
        for art_decision in [ART_CONTINUED, ART_STOPPED]:
            with self.subTest(art_decision):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "ever_on_art": YES,
                        "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                        "initial_art_date_estimated": NO,
                        "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                        "has_switched_art_regimen": NO,
                        "has_defaulted": YES,
                        "defaulted_date": self.hiv_dx_date + relativedelta(days=14),
                        "defaulted_date_estimated": "D",
                        "is_adherent": DEFAULTED,
                        "art_doses_missed": None,
                        "art_decision": art_decision,
                    }
                )
                form_validator = ArvHistoryFormValidator(
                    cleaned_data=cleaned_data, model=ArvHistoryMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("art_decision", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable",
                    str(cm.exception.error_dict.get("art_decision")),
                )

    def test_art_decision_applicable_if_has_defaulted_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "ever_on_art": YES,
                "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                "initial_art_date_estimated": NO,
                "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                "has_switched_art_regimen": NO,
                "has_defaulted": NO,
                "defaulted_date": None,
                "defaulted_date_estimated": NOT_APPLICABLE,
                "is_adherent": YES,
                "art_doses_missed": None,
                "art_decision": NOT_APPLICABLE,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("art_decision", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable",
            str(cm.exception.error_dict.get("art_decision")),
        )

    def test_art_decision_choices_with_has_defaulted_no_ok(self):
        for art_decision in [ART_CONTINUED, ART_STOPPED]:
            with self.subTest(art_decision):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "ever_on_art": YES,
                        "initial_art_date": self.hiv_dx_date + relativedelta(days=7),
                        "initial_art_date_estimated": NO,
                        "initial_art_regimen": MockSet(self.arv_regimens_choice_abc_3tc_ftc),
                        "has_switched_art_regimen": NO,
                        "has_defaulted": NO,
                        "defaulted_date": None,
                        "defaulted_date_estimated": NOT_APPLICABLE,
                        "is_adherent": YES,
                        "art_doses_missed": None,
                        "art_decision": art_decision,
                    }
                )
                form_validator = ArvHistoryFormValidator(
                    cleaned_data=cleaned_data, model=ArvHistoryMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_arv_history_cd4_date_after_hiv_dx_date_ok(self):
        hiv_dx_date = self.screening_datetime.date() - relativedelta(days=7)
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                # HIV Diagnosis
                "hiv_dx_date": hiv_dx_date,
                "hiv_dx_date_estimated": NO,
                # CD4 count
                "cd4_value": 80,
                "cd4_date": hiv_dx_date + relativedelta(days=1),
                "cd4_date_estimated": NO,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_arv_history_cd4_date_matches_hiv_dx_date_ok(self):
        hiv_dx_date = self.screening_datetime.date() - relativedelta(days=7)
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                # HIV Diagnosis
                "hiv_dx_date": hiv_dx_date,
                "hiv_dx_date_estimated": NO,
                # CD4 count
                "cd4_value": 80,
                "cd4_date": hiv_dx_date,
                "cd4_date_estimated": NO,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_arv_history_cd4_date_before_hiv_dx_date_raises(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                # HIV Diagnosis
                "hiv_dx_date": self.hiv_dx_date,
                "hiv_dx_date_estimated": NO,
                # CD4 count
                "cd4_value": 80,
                "cd4_date": self.hiv_dx_date - relativedelta(days=1),
                "cd4_date_estimated": NO,
            }
        )
        form_validator = ArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("cd4_date", cm.exception.error_dict)
        self.assertIn(
            "Invalid. Cannot be before 'HIV diagnosis first known' date",
            cm.exception.error_dict.get("cd4_date")[0].message,
        )

    def test_matching_arv_history_and_screening_cd4_data_ok(self):
        screening_cd4_date = self.hiv_dx_date + relativedelta(days=7)

        class OverriddenArvHistoryFormValidator(FormValidatorTestMixin, Base):
            @property
            def subject_screening(self):
                return MockModel(
                    mock_name="SubjectScreening",
                    subject_identifier=self.subject_identifier,
                    cd4_value=80,
                    cd4_date=screening_cd4_date,
                )

        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                # CD4 count
                "cd4_value": 80,
                "cd4_date": screening_cd4_date,
                "cd4_date_estimated": NO,
            }
        )
        form_validator = OverriddenArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_matching_arv_history_and_screening_cd4_dates_with_differing_cd4_values_raises(
        self,
    ):
        screening_cd4_date = self.hiv_dx_date + relativedelta(days=7)

        class OverriddenArvHistoryFormValidator(FormValidatorTestMixin, Base):
            @property
            def subject_screening(self):
                return MockModel(
                    mock_name="SubjectScreening",
                    subject_identifier=self.subject_identifier,
                    cd4_value=79,
                    cd4_date=screening_cd4_date,
                )

        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                # CD4 count
                "cd4_value": 80,
                "cd4_date": screening_cd4_date,
                "cd4_date_estimated": NO,
            }
        )
        form_validator = OverriddenArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("cd4_value", cm.exception.error_dict)
        self.assertIn(
            "Invalid. Cannot differ from screening CD4 count "
            "(79) if collected on same date.",
            cm.exception.error_dict.get("cd4_value")[0].message,
        )

    def test_arv_history_cd4_date_before_screening_cd4_date_raises(self):
        screening_cd4_date = self.hiv_dx_date + relativedelta(days=7)

        class OverriddenArvHistoryFormValidator(FormValidatorTestMixin, Base):
            @property
            def subject_screening(self):
                return MockModel(
                    mock_name="SubjectScreening",
                    subject_identifier=self.subject_identifier,
                    cd4_value=80,
                    cd4_date=screening_cd4_date,
                )

        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                # CD4 count
                "cd4_value": 80,
                "cd4_date": screening_cd4_date - relativedelta(days=1),
                "cd4_date_estimated": NO,
            }
        )
        form_validator = OverriddenArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("cd4_date", cm.exception.error_dict)
        self.assertIn(
            f"Invalid. Cannot be before screening CD4 date ({screening_cd4_date}).",
            cm.exception.error_dict.get("cd4_date")[0].message,
        )

    def test_arv_history_cd4_date_after_screening_cd4_date_ok(self):
        screening_cd4_date = self.hiv_dx_date

        class OverriddenArvHistoryFormValidator(FormValidatorTestMixin, Base):
            @property
            def subject_screening(self):
                return MockModel(
                    mock_name="SubjectScreening",
                    subject_identifier=self.subject_identifier,
                    cd4_value=80,
                    cd4_date=screening_cd4_date,
                )

        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                # CD4 count
                "cd4_value": 80,
                "cd4_date": screening_cd4_date + relativedelta(days=1),
                "cd4_date_estimated": NO,
            }
        )
        form_validator = OverriddenArvHistoryFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    @override_settings(SUBJECT_SCREENING_MODEL="effect_screening.subjectscreening")
    def test_subject_screening_property_present(self):
        """Tests only that subject_screening property is present in form
        validator class.
        """
        cleaned_data = self.get_cleaned_data()
        form_validator = ArvHistoryWithoutSubjectScreeningMockFormValidator(
            cleaned_data=cleaned_data, model=ArvHistoryMockModel
        )
        try:
            form_validator.validate()
        except AttributeError as e:
            self.fail(f"AttributeError unexpectedly raised. Got {e}")
        except LookupError:
            pass
