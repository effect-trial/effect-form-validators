from django.core.exceptions import ValidationError
from django.test import TestCase
from django_mock_queries.query import MockModel, MockSet
from edc_constants.constants import NO, NOT_APPLICABLE, OTHER, YES
from edc_constants.disease_constants import BACTERAEMIA
from edc_form_validators.tests.mixins import FormValidatorTestMixin

from effect_form_validators.effect_subject import DiagnosesFormValidator as Base

from ..mixins import TestCaseMixin


class DiagnosesMockModel(MockModel):
    @classmethod
    def related_visit_model_attr(cls):
        return "subject_visit"


class DiagnosesFormValidator(FormValidatorTestMixin, Base):
    pass


class TestDiagnosesFormValidator(TestCaseMixin, TestCase):
    reportable_fields = ["reportable_as_ae", "patient_admitted"]

    def setUp(self) -> None:
        super().setUp()
        self.diagnoses_choice_na = MockModel(
            mock_name="Diagnoses", name=NOT_APPLICABLE, display_name=NOT_APPLICABLE
        )
        self.diagnoses_choice_bacteraemia = MockModel(
            mock_name="Diagnoses", name=BACTERAEMIA, display_name=BACTERAEMIA
        )
        self.diagnoses_choice_other = MockModel(
            mock_name="Diagnoses", name=OTHER, display_name=OTHER
        )

    def get_cleaned_data(self, **kwargs) -> dict:
        cleaned_data = super().get_cleaned_data(**kwargs)
        cleaned_data.update(
            gi_side_effects=NO,
            gi_side_effects_details="",
            has_diagnoses=NO,
            diagnoses=MockSet(self.diagnoses_choice_na),
            diagnoses_other="",
            reportable_as_ae=NOT_APPLICABLE,
            patient_admitted=NOT_APPLICABLE,
        )
        return cleaned_data

    def test_cleaned_data_ok(self):
        cleaned_data = self.get_cleaned_data()
        form_validator = DiagnosesFormValidator(
            cleaned_data=cleaned_data, model=DiagnosesMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_gi_side_effects_details_required_if_gi_side_effects_YES(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "gi_side_effects": YES,
                "gi_side_effects_details": "",
            }
        )
        form_validator = DiagnosesFormValidator(
            cleaned_data=cleaned_data, model=DiagnosesMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("gi_side_effects_details", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("gi_side_effects_details")),
        )

        cleaned_data.update(
            {
                "gi_side_effects": YES,
                "gi_side_effects_details": "some details",
                "reportable_as_ae": NO,
                "patient_admitted": NO,
            }
        )
        form_validator = DiagnosesFormValidator(
            cleaned_data=cleaned_data, model=DiagnosesMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_gi_side_effects_details_not_required_if_gi_side_effects_NO(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "gi_side_effects": NO,
                "gi_side_effects_details": "some details",
            }
        )
        form_validator = DiagnosesFormValidator(
            cleaned_data=cleaned_data, model=DiagnosesMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("gi_side_effects_details", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("gi_side_effects_details")),
        )

        cleaned_data.update(
            {
                "gi_side_effects": NO,
                "gi_side_effects_details": "",
            }
        )
        form_validator = DiagnosesFormValidator(
            cleaned_data=cleaned_data, model=DiagnosesMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_m2m_diagnoses_NA_raises_if_has_diagnoses_YES(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "has_diagnoses": YES,
                "diagnoses": MockSet(self.diagnoses_choice_na),
                "diagnoses_other": "",
                "reportable_as_ae": NO,
                "patient_admitted": NO,
            }
        )
        form_validator = DiagnosesFormValidator(
            cleaned_data=cleaned_data, model=DiagnosesMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("diagnoses", cm.exception.error_dict)
        self.assertIn(
            "Invalid selection. "
            "Cannot be N/A if there are significant diagnoses to report.",
            str(cm.exception.error_dict.get("diagnoses")),
        )

        cleaned_data.update(
            {
                "has_diagnoses": YES,
                "diagnoses": MockSet(self.diagnoses_choice_bacteraemia),
                "diagnoses_other": "",
            }
        )
        form_validator = DiagnosesFormValidator(
            cleaned_data=cleaned_data, model=DiagnosesMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_m2m_diagnoses_expects_NA_if_has_diagnoses_NO(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "has_diagnoses": NO,
                "diagnoses": MockSet(self.diagnoses_choice_bacteraemia),
                "diagnoses_other": "",
            }
        )
        form_validator = DiagnosesFormValidator(
            cleaned_data=cleaned_data, model=DiagnosesMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("diagnoses", cm.exception.error_dict)
        self.assertIn(
            "Expected N/A only if NO significant diagnoses to report.",
            str(cm.exception.error_dict.get("diagnoses")),
        )

        cleaned_data.update(
            {
                "has_diagnoses": NO,
                "diagnoses": MockSet(self.diagnoses_choice_na),
                "diagnoses_other": "",
            }
        )
        form_validator = DiagnosesFormValidator(
            cleaned_data=cleaned_data, model=DiagnosesMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_diagnoses_other_required_if_diagnoses_OTHER(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "has_diagnoses": YES,
                "diagnoses": MockSet(self.diagnoses_choice_other),
                "diagnoses_other": "",
                "reportable_as_ae": NO,
                "patient_admitted": NO,
            }
        )
        form_validator = DiagnosesFormValidator(
            cleaned_data=cleaned_data, model=DiagnosesMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("diagnoses_other", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("diagnoses_other")),
        )

        cleaned_data.update(
            {
                "has_diagnoses": YES,
                "diagnoses": MockSet(self.diagnoses_choice_other),
                "diagnoses_other": "some other diagnosis",
            }
        )
        form_validator = DiagnosesFormValidator(
            cleaned_data=cleaned_data, model=DiagnosesMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_diagnoses_other_not_required_if_diagnoses_not_OTHER(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "has_diagnoses": YES,
                "diagnoses": MockSet(self.diagnoses_choice_bacteraemia),
                "diagnoses_other": "some other diagnosis",
                "reportable_as_ae": NO,
                "patient_admitted": NO,
            }
        )
        form_validator = DiagnosesFormValidator(
            cleaned_data=cleaned_data, model=DiagnosesMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("diagnoses_other", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("diagnoses_other")),
        )

        cleaned_data.update(
            {
                "has_diagnoses": YES,
                "diagnoses": MockSet(self.diagnoses_choice_bacteraemia),
                "diagnoses_other": "",
            }
        )
        form_validator = DiagnosesFormValidator(
            cleaned_data=cleaned_data, model=DiagnosesMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reporting_fields_applicable_if_gi_side_effects_YES(self):
        for reporting_fld_answer in [YES, NO]:
            with self.subTest(
                reporting_fld_answer=reporting_fld_answer,
            ):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "gi_side_effects": YES,
                        "gi_side_effects_details": "some details",
                        "reportable_as_ae": NOT_APPLICABLE,
                        "patient_admitted": NOT_APPLICABLE,
                    }
                )

                form_validator = DiagnosesFormValidator(
                    cleaned_data=cleaned_data, model=DiagnosesMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("reportable_as_ae", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("reportable_as_ae")),
                )

                cleaned_data.update({"reportable_as_ae": reporting_fld_answer})
                form_validator = DiagnosesFormValidator(
                    cleaned_data=cleaned_data, model=DiagnosesMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("patient_admitted", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("patient_admitted")),
                )

                cleaned_data.update({"patient_admitted": reporting_fld_answer})
                form_validator = DiagnosesFormValidator(
                    cleaned_data=cleaned_data, model=DiagnosesMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reporting_fields_not_applicable_if_gi_side_effects_NO(self):
        for reporting_fld in self.reportable_fields:
            for reporting_fld_answer in [YES, NO]:
                with self.subTest(
                    reporting_fld=reporting_fld,
                    reporting_fld_answer=reporting_fld_answer,
                ):
                    cleaned_data = self.get_cleaned_data()
                    cleaned_data.update(
                        {
                            "gi_side_effects": NO,
                            "gi_side_effects_details": "",
                            reporting_fld: reporting_fld_answer,
                        }
                    )

                    form_validator = DiagnosesFormValidator(
                        cleaned_data=cleaned_data, model=DiagnosesMockModel
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn(reporting_fld, cm.exception.error_dict)
                    self.assertIn(
                        "This field is not applicable.",
                        str(cm.exception.error_dict.get(reporting_fld)),
                    )

                    cleaned_data.update({reporting_fld: NOT_APPLICABLE})
                    form_validator = DiagnosesFormValidator(
                        cleaned_data=cleaned_data, model=DiagnosesMockModel
                    )
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reporting_fields_applicable_if_has_diagnoses_YES(self):
        for reporting_fld_answer in [YES, NO]:
            with self.subTest(
                reporting_fld_answer=reporting_fld_answer,
            ):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "has_diagnoses": YES,
                        "diagnoses": MockSet(self.diagnoses_choice_bacteraemia),
                        "reportable_as_ae": NOT_APPLICABLE,
                        "patient_admitted": NOT_APPLICABLE,
                    }
                )

                form_validator = DiagnosesFormValidator(
                    cleaned_data=cleaned_data, model=DiagnosesMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("reportable_as_ae", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("reportable_as_ae")),
                )

                cleaned_data.update({"reportable_as_ae": reporting_fld_answer})
                form_validator = DiagnosesFormValidator(
                    cleaned_data=cleaned_data, model=DiagnosesMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("patient_admitted", cm.exception.error_dict)
                self.assertIn(
                    "This field is applicable.",
                    str(cm.exception.error_dict.get("patient_admitted")),
                )

                cleaned_data.update({"patient_admitted": reporting_fld_answer})
                form_validator = DiagnosesFormValidator(
                    cleaned_data=cleaned_data, model=DiagnosesMockModel
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reporting_fields_not_applicable_if_has_diagnoses_NO(self):
        for reporting_fld in self.reportable_fields:
            for reporting_fld_answer in [YES, NO]:
                with self.subTest(
                    reporting_fld=reporting_fld,
                    reporting_fld_answer=reporting_fld_answer,
                ):
                    cleaned_data = self.get_cleaned_data()
                    cleaned_data.update(
                        {
                            "has_diagnoses": NO,
                            "diagnoses": MockSet(),
                            reporting_fld: reporting_fld_answer,
                        }
                    )

                    form_validator = DiagnosesFormValidator(
                        cleaned_data=cleaned_data, model=DiagnosesMockModel
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn(reporting_fld, cm.exception.error_dict)
                    self.assertIn(
                        "This field is not applicable.",
                        str(cm.exception.error_dict.get(reporting_fld)),
                    )

                    cleaned_data.update({reporting_fld: NOT_APPLICABLE})
                    form_validator = DiagnosesFormValidator(
                        cleaned_data=cleaned_data, model=DiagnosesMockModel
                    )
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")
