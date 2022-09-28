from dateutil.relativedelta import relativedelta
from django import forms
from django.test import TestCase
from django_mock_queries.query import MockModel, MockSet
from edc_constants.constants import NO, NOT_APPLICABLE
from edc_utils import get_utcnow, get_utcnow_as_date

from effect_form_validators.effect_subject import ArvHistoryFormValidator as Base

from ..mixins import FormValidatorTestMixin, TestCaseMixin


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


class TestArvHistoryFormValidator(TestCaseMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.hiv_dx_date = self.screening_datetime.date() - relativedelta(days=30)

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
        except forms.ValidationError as e:
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
        except forms.ValidationError as e:
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
        except forms.ValidationError as e:
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
        with self.assertRaises(forms.ValidationError) as cm:
            form_validator.validate()
        self.assertIn("hiv_dx_date", cm.exception.error_dict)
        self.assertIn(
            f"Invalid. Cannot be after screening CD4 date ({screening_cd4_date}).",
            cm.exception.error_dict.get("hiv_dx_date")[0].message,
        )

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
        except forms.ValidationError as e:
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
        except forms.ValidationError as e:
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
        with self.assertRaises(forms.ValidationError) as cm:
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
        except forms.ValidationError as e:
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
        with self.assertRaises(forms.ValidationError) as cm:
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
        with self.assertRaises(forms.ValidationError) as cm:
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
        except forms.ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")
