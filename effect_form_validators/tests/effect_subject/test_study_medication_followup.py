from typing import Optional
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.test import TestCase, tag
from django_mock_queries.query import MockModel, MockSet
from edc_constants.constants import NO, NOT_APPLICABLE, OTHER, YES
from edc_utils import get_utcnow
from edc_visit_schedule.constants import DAY01, DAY03, DAY14, WEEK10

from effect_form_validators.effect_subject import (
    StudyMedicationFollowupFormValidator as Base,
)

from ..mixins import FormValidatorTestMixin, TestCaseMixin


class StudyMedicationFollowupFormValidator(FormValidatorTestMixin, Base):
    pass


@tag("debug")
class TestStudyMedicationFollowupFormValidation(TestCaseMixin, TestCase):

    flucyt_individual_dose_fields = [
        f"flucyt_dose_{hr}" for hr in ["0400", "1000", "1600", "2200"]
    ]

    def setUp(self) -> None:
        super().setUp()
        sm_baseline_patcher = patch(
            "effect_form_validators.effect_subject"
            ".study_medication_followup_form_validator.is_baseline"
        )
        self.addCleanup(sm_baseline_patcher.stop)
        self.mock_is_baseline = sm_baseline_patcher.start()

        self.modifications_choice_per_protocol = MockModel(
            mock_name="DoseModificationReasons",
            name="per_protocol",
            display_name="per_protocol",
        )

        self.modifications_choice_renal_adjustment = MockModel(
            mock_name="DoseModificationReasons",
            name="renal_adjustment",
            display_name="renal_adjustment",
        )

        self.modifications_choice_toxicity = MockModel(
            mock_name="DoseModificationReasons",
            name="toxicity",
            display_name="toxicity",
        )

        self.modifications_choice_other = MockModel(
            mock_name="DoseModificationReasons",
            name=OTHER,
            display_name=OTHER,
        )

    def get_cleaned_data(
        self,
        visit_code: Optional[str] = None,
        visit_code_sequence: Optional[int] = None,
        **kwargs,
    ) -> dict:
        cleaned_data = super().get_cleaned_data(
            visit_code=visit_code,
            visit_code_sequence=visit_code_sequence,
            report_datetime=kwargs.get("report_datetime", get_utcnow()),
        )
        cleaned_data.update(
            {
                # Modifications
                "modifications": YES,
                "modifications_reason": MockSet(self.modifications_choice_per_protocol),
                "modifications_reason_other": "",
                # Flucon
                "flucon_modified": YES,
                "flucon_dose_datetime": get_utcnow() + relativedelta(minutes=1),
                "flucon_dose": 800,
                "flucon_notes": "",
                # Flucyt
                "flucyt_modified": YES,
                "flucyt_dose_datetime": get_utcnow() + relativedelta(minutes=1),
                "flucyt_dose_rx": 0,
                "flucyt_dose_0400": 0,
                "flucyt_dose_1000": 0,
                "flucyt_dose_1600": 0,
                "flucyt_dose_2200": 0,
                "flucyt_notes": "",
            }
        )

        return cleaned_data

    def test_cleaned_data_after_baseline_ok(self):
        self.mock_is_baseline.return_value = False
        for visit_code in self.visit_schedule:
            for seq in [0, 1, 2]:
                if visit_code == DAY01 and seq == 0:
                    break

                with self.subTest(visit_code=visit_code, visit_code_sequence=seq):
                    cleaned_data = self.get_cleaned_data(
                        visit_code=visit_code,
                        visit_code_sequence=seq,
                    )
                    form_validator = StudyMedicationFollowupFormValidator(
                        cleaned_data=cleaned_data
                    )
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_at_baseline_raises(self):
        self.mock_is_baseline.return_value = True
        cleaned_data = self.get_cleaned_data(visit_code=DAY01, visit_code_sequence=0)
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("__all__", cm.exception.error_dict)
        self.assertIn(
            "This form may not be completed at baseline",
            str(cm.exception.error_dict.get("__all__")),
        )

    # Modifications tests
    def test_modifications_reason_required_if_modifications_yes(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                "modifications": YES,
                "modifications_reason": MockSet(),
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("modifications_reason", cm.exception.error_dict)
        self.assertIn(
            "This field is required",
            str(cm.exception.error_dict.get("modifications_reason")),
        )

    def test_modifications_reason_not_required_if_modifications_no(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                "modifications": NO,
                "modifications_reason": MockSet(self.modifications_choice_per_protocol),
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("modifications_reason", cm.exception.error_dict)
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("modifications_reason")),
        )

    def test_modifications_reason_per_protocol_with_other_selections_raises(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                "modifications": YES,
                "modifications_reason": MockSet(
                    self.modifications_choice_per_protocol,
                    self.modifications_choice_renal_adjustment,
                    self.modifications_choice_toxicity,
                ),
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("modifications_reason", cm.exception.error_dict)
        self.assertIn(
            "Invalid combination. 'per_protocol' may not be combined with other selections",
            str(cm.exception.error_dict.get("modifications_reason")),
        )

        cleaned_data.update(
            {
                "modifications": YES,
                "modifications_reason": MockSet(
                    self.modifications_choice_per_protocol,
                    self.modifications_choice_toxicity,
                ),
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("modifications_reason", cm.exception.error_dict)
        self.assertIn(
            "Invalid combination. 'per_protocol' may not be combined with other selections",
            str(cm.exception.error_dict.get("modifications_reason")),
        )

    def test_modifications_reason_per_protocol_single_selection_ok(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                "modifications": YES,
                "modifications_reason": MockSet(self.modifications_choice_per_protocol),
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_modifications_reason_with_multiple_selections_ok(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                "modifications": YES,
                "modifications_reason": MockSet(
                    self.modifications_choice_renal_adjustment,
                    self.modifications_choice_toxicity,
                    self.modifications_choice_other,
                ),
                "modifications_reason_other": "Some other reason...",
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_modifications_reason_other_required_if_other_selected(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                "modifications": YES,
                "modifications_reason": MockSet(self.modifications_choice_other),
                "modifications_reason_other": "",
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("modifications_reason_other", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("modifications_reason_other")),
        )

    def test_modifications_reason_other_not_required_if_other_not_selected(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                "modifications": YES,
                "modifications_reason": MockSet(self.modifications_choice_toxicity),
                "modifications_reason_other": "Some other reason",
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("modifications_reason_other", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("modifications_reason_other")),
        )

    def test_modifications_yes_with_no_modifications_reported_raises(self):
        self.mock_is_baseline.return_value = False
        for flucon_answer in [NO, NOT_APPLICABLE]:
            for flucyt_answer in [NO, NOT_APPLICABLE]:
                with self.subTest(flucon_modified=flucon_answer, flucyt_answer=flucyt_answer):
                    cleaned_data = self.get_cleaned_data(
                        visit_code=DAY03, visit_code_sequence=0
                    )
                    cleaned_data.update(
                        {
                            # Modifications
                            "modifications": YES,
                            "modifications_reason": MockSet(
                                self.modifications_choice_per_protocol
                            ),
                            "modifications_reason_other": "",
                            # Flucon
                            "flucon_modified": flucon_answer,
                            # Flucyt
                            "flucyt_modified": flucyt_answer,
                        }
                    )
                    form_validator = StudyMedicationFollowupFormValidator(
                        cleaned_data=cleaned_data
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn("flucon_modified", cm.exception.error_dict)
                    self.assertIn("flucyt_modified", cm.exception.error_dict)
                    error_msg = (
                        "Invalid. "
                        "Expected at least one modification in "
                        "'Fluconazole' or 'Flucytosine' section."
                    )
                    self.assertIn(
                        error_msg, str(cm.exception.error_dict.get("flucon_modified"))
                    )
                    self.assertIn(
                        error_msg, str(cm.exception.error_dict.get("flucyt_modified"))
                    )

    def test_modifications_yes_with_only_flucon_modifications_ok(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                # Modifications
                "modifications": YES,
                "modifications_reason": MockSet(self.modifications_choice_per_protocol),
                "modifications_reason_other": "",
                # Flucon
                "flucon_modified": YES,
                # Flucyt
                "flucyt_modified": NO,
                "flucyt_dose_datetime": None,
                "flucyt_dose_rx": None,
                "flucyt_dose_0400": None,
                "flucyt_dose_1000": None,
                "flucyt_dose_1600": None,
                "flucyt_dose_2200": None,
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_modifications_yes_with_only_flucyt_modifications_ok(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                # Modifications
                "modifications": YES,
                "modifications_reason": MockSet(self.modifications_choice_per_protocol),
                "modifications_reason_other": "",
                # Flucon
                "flucon_modified": NO,
                "flucon_dose_datetime": None,
                "flucon_dose": None,
                # Flucyt
                "flucyt_modified": YES,
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    # Flucon tests
    def test_flucon_modified_not_applicable_if_modifications_no(self):
        self.mock_is_baseline.return_value = False
        for answer in [YES, NO]:
            with self.subTest(flucon_modified=answer):
                cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
                cleaned_data.update(
                    {
                        "modifications": NO,
                        "modifications_reason": MockSet(),
                        "flucon_modified": answer,
                    }
                )
                form_validator = StudyMedicationFollowupFormValidator(
                    cleaned_data=cleaned_data
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("flucon_modified", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable.",
                    str(cm.exception.error_dict.get("flucon_modified")),
                )

    def test_flucon_dose_datetime_required_if_flucon_modified_yes(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_modified": YES,
                "flucon_dose_datetime": None,
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_datetime", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucon_dose_datetime")),
        )

    def test_flucon_dose_datetime_not_required_if_flucon_modified_no(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_modified": NO,
                "flucon_dose_datetime": get_utcnow() + relativedelta(minutes=1),
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_datetime", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("flucon_dose_datetime")),
        )

    # def test_flucon_flucyt_dose_datetime_equal_report_datetime_ok(self):
    #     self.mock_is_baseline.return_value = False
    #     report_datetime = get_utcnow() - relativedelta(days=14)
    #     cleaned_data = self.get_cleaned_data(
    #         visit_code=DAY01,
    #         visit_code_sequence=0,
    #         report_datetime=report_datetime,
    #     )
    #     cleaned_data.update(
    #         {
    #             "flucon_dose_datetime": report_datetime,
    #             "flucyt_dose_datetime": report_datetime,
    #         }
    #     )
    #     form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
    #     try:
    #         form_validator.validate()
    #     except ValidationError as e:
    #         self.fail(f"ValidationError unexpectedly raised. Got {e}")
    #
    # def test_flucon_dose_datetime_before_report_datetime_raises(self):
    #     self.mock_is_baseline.return_value = False
    #     report_datetime = get_utcnow()
    #     cleaned_data = self.get_cleaned_data(
    #         visit_code=DAY01,
    #         visit_code_sequence=0,
    #         report_datetime=report_datetime,
    #     )
    #     cleaned_data.update(
    #         {"flucon_dose_datetime": report_datetime - relativedelta(days=1)}
    #     )
    #     form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
    #     with self.assertRaises(ValidationError) as cm:
    #         form_validator.validate()
    #     self.assertIn("flucon_dose_datetime", cm.exception.error_dict)
    #     self.assertIn(
    #         f"Expected {formatted_date(report_datetime)}",
    #         str(cm.exception.error_dict.get("flucon_dose_datetime")),
    #     )
    #
    # def test_flucon_dose_datetime_after_report_datetime_raises(self):
    #     self.mock_is_baseline.return_value = False
    #     report_datetime = get_utcnow()
    #     cleaned_data = self.get_cleaned_data(
    #         visit_code=DAY01,
    #         visit_code_sequence=0,
    #         report_datetime=report_datetime,
    #     )
    #     cleaned_data.update(
    #         {"flucon_dose_datetime": report_datetime + relativedelta(days=1)}
    #     )
    #     form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
    #     with self.assertRaises(ValidationError) as cm:
    #         form_validator.validate()
    #     self.assertIn("flucon_dose_datetime", cm.exception.error_dict)
    #     self.assertIn(
    #         f"Expected {formatted_date(report_datetime)}",
    #         str(cm.exception.error_dict.get("flucon_dose_datetime")),
    #     )
    #
    def test_flucon_dose_required_if_flucon_modified_yes(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_modified": YES,
                "flucon_dose": None,
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucon_dose")),
        )

    def test_flucon_dose_not_required_if_flucon_modified_no(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_modified": NO,
                "flucon_dose_datetime": None,
                "flucon_dose": 1200,
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("flucon_dose")),
        )

    def test_flucon_notes_not_required_if_flucon_modified_na(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_modified": NOT_APPLICABLE,
                "flucon_dose_datetime": None,
                "flucon_dose": None,
                "flucon_notes": "Some flucon notes here",
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_notes", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("flucon_notes")),
        )

    # def test_flucon_notes_required_baseline_flucon_dose_not_1200(self):
    #     self.mock_is_baseline.return_value = False
    #     cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
    #     cleaned_data.update(
    #         {
    #             "flucon_modified": YES,
    #             "flucon_dose": 800,
    #             "flucon_notes": "",
    #         }
    #     )
    #     form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
    #     with self.assertRaises(ValidationError) as cm:
    #         form_validator.validate()
    #     self.assertIn("flucon_notes", cm.exception.error_dict)
    #     self.assertIn(
    #         "This field is required. Fluconazole dose not 1200 mg/d.",
    #         str(cm.exception.error_dict.get("flucon_notes")),
    #     )
    #
    def test_flucon_notes_with_d14_flucon_dose_800_ok(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY14, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_modified": YES,
                "flucon_dose": 800,
                "flucon_notes": "Some other flucon notes here",
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucon_notes_with_w10_flucon_dose_200_ok(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=WEEK10, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucon_modified": YES,
                "flucon_dose": 200,
                "flucon_notes": "Some other flucon notes here",
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    # Flucyt tests
    def test_flucyt_modified_not_applicable_if_modifications_no(self):
        self.mock_is_baseline.return_value = False
        for answer in [YES, NO]:
            with self.subTest(flucon_modified=answer):
                cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
                cleaned_data.update(
                    {
                        "modifications": NO,
                        "modifications_reason": MockSet(),
                        "flucon_modified": NOT_APPLICABLE,
                        "flucon_dose_datetime": None,
                        "flucon_dose": None,
                        "flucyt_modified": answer,
                    }
                )
                form_validator = StudyMedicationFollowupFormValidator(
                    cleaned_data=cleaned_data
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("flucyt_modified", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable.",
                    str(cm.exception.error_dict.get("flucyt_modified")),
                )

    def test_flucyt_modified_can_be_not_applicable(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                # Modifications
                "modifications": YES,
                "modifications_reason": MockSet(self.modifications_choice_per_protocol),
                "modifications_reason_other": "",
                # Flucon
                "flucon_modified": YES,
                # Flucyt
                "flucyt_modified": NOT_APPLICABLE,
                "flucyt_dose_datetime": None,
                "flucyt_dose_rx": None,
                "flucyt_dose_0400": None,
                "flucyt_dose_1000": None,
                "flucyt_dose_1600": None,
                "flucyt_dose_2200": None,
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucyt_dose_datetime_required_if_flucyt_modified_yes(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucyt_modified": YES,
                "flucyt_dose_datetime": None,
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucyt_dose_datetime", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucyt_dose_datetime")),
        )

    def test_flucyt_dose_datetime_not_required_if_flucyt_modified_not_yes(self):
        self.mock_is_baseline.return_value = False
        for answer in [NO, NOT_APPLICABLE]:
            with self.subTest(flucyt_modified=answer):
                cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
                cleaned_data.update(
                    {
                        "flucyt_modified": answer,
                        "flucyt_dose_datetime": get_utcnow() + relativedelta(minutes=1),
                    }
                )
                form_validator = StudyMedicationFollowupFormValidator(
                    cleaned_data=cleaned_data
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("flucyt_dose_datetime", cm.exception.error_dict)
                self.assertIn(
                    "This field is not required.",
                    str(cm.exception.error_dict.get("flucyt_dose_datetime")),
                )

    # def test_flucyt_dose_datetime_before_report_datetime_raises(self):
    #     self.mock_is_baseline.return_value = False
    #     report_datetime = get_utcnow()
    #     cleaned_data = self.get_cleaned_data(
    #         visit_code=DAY01,
    #         visit_code_sequence=0,
    #         report_datetime=report_datetime,
    #     )
    #     cleaned_data.update(
    #         {"flucyt_dose_datetime": report_datetime - relativedelta(days=1)}
    #     )
    #     form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
    #     with self.assertRaises(ValidationError) as cm:
    #         form_validator.validate()
    #     self.assertIn("flucyt_dose_datetime", cm.exception.error_dict)
    #     self.assertIn(
    #         f"Expected {formatted_date(report_datetime)}",
    #         str(cm.exception.error_dict.get("flucyt_dose_datetime")),
    #     )
    #
    # def test_flucyt_dose_datetime_after_report_datetime_raises(self):
    #     self.mock_is_baseline.return_value = False
    #     report_datetime = get_utcnow()
    #     cleaned_data = self.get_cleaned_data(
    #         visit_code=DAY01,
    #         visit_code_sequence=0,
    #         report_datetime=report_datetime,
    #     )
    #     cleaned_data.update(
    #         {"flucyt_dose_datetime": report_datetime + relativedelta(days=1)}
    #     )
    #     form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
    #     with self.assertRaises(ValidationError) as cm:
    #         form_validator.validate()
    #     self.assertIn("flucyt_dose_datetime", cm.exception.error_dict)
    #     self.assertIn(
    #         f"Expected {formatted_date(report_datetime)}",
    #         str(cm.exception.error_dict.get("flucyt_dose_datetime")),
    #     )
    #
    def test_flucyt_dose_rx_required_if_flucyt_modified_yes(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update({"flucyt_dose_rx": None})
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucyt_dose_rx", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucyt_dose_rx")),
        )

    def test_flucyt_dose_rx_not_required_if_flucyt_modified_not_yes(self):
        self.mock_is_baseline.return_value = False
        for answer in [NO, NOT_APPLICABLE]:
            with self.subTest(flucyt_modified=answer):
                cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
                cleaned_data.update(
                    {
                        "flucyt_modified": answer,
                        "flucyt_dose_datetime": None,
                        "flucyt_dose_rx": 100,
                    }
                )
                form_validator = StudyMedicationFollowupFormValidator(
                    cleaned_data=cleaned_data
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("flucyt_dose_rx", cm.exception.error_dict)
                self.assertIn(
                    "This field is not required.",
                    str(cm.exception.error_dict.get("flucyt_dose_rx")),
                )

    def test_individual_flucyt_doses_required_if_flucyt_modified_yes(self):
        self.mock_is_baseline.return_value = False
        for dose_field in self.flucyt_individual_dose_fields:
            with self.subTest(dose_field=dose_field):
                cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
                cleaned_data.update({dose_field: None})
                form_validator = StudyMedicationFollowupFormValidator(
                    cleaned_data=cleaned_data
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn(dose_field, cm.exception.error_dict)
                self.assertIn(
                    "This field is required.",
                    str(cm.exception.error_dict.get(dose_field)),
                )

    def test_individual_flucyt_doses_not_required_if_flucyt_modified_not_yes(self):
        self.mock_is_baseline.return_value = False
        for answer in [NO, NOT_APPLICABLE]:
            for dose_field in self.flucyt_individual_dose_fields:
                with self.subTest(answer=answer, dose_field=dose_field):
                    cleaned_data = self.get_cleaned_data(
                        visit_code=DAY01, visit_code_sequence=0
                    )
                    cleaned_data.update(
                        {
                            "flucyt_modified": answer,
                            "flucyt_dose_datetime": None,
                            "flucyt_dose_rx": None,
                            # Reset all individual doses to None
                            "flucyt_dose_0400": None,
                            "flucyt_dose_1000": None,
                            "flucyt_dose_1600": None,
                            "flucyt_dose_2200": None,
                        }
                    )
                    # Update individual dose being tested
                    cleaned_data.update({dose_field: 1000})
                    form_validator = StudyMedicationFollowupFormValidator(
                        cleaned_data=cleaned_data
                    )
                    with self.assertRaises(ValidationError) as cm:
                        form_validator.validate()
                    self.assertIn(dose_field, cm.exception.error_dict)
                    self.assertIn(
                        "This field is not required.",
                        str(cm.exception.error_dict.get(dose_field)),
                    )

    def test_all_doses_can_be_zero_if_flucyt_modified_yes(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY14, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucyt_dose_rx": 0,
                "flucyt_dose_0400": 0,
                "flucyt_dose_1000": 0,
                "flucyt_dose_1600": 0,
                "flucyt_dose_2200": 0,
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_sum_individual_flucyt_doses_eq_flucyt_dose_rx_ok(self):
        self.mock_is_baseline.return_value = False
        dose_schedules = (
            (1000, 1000, 1000, 1000),
            (0, 2000, 2000, 0),
            (500, 1500, 1500, 500),
            (700, 1000, 300, 2000),
        )
        for schedule in dose_schedules:
            with self.subTest(schedule=schedule):
                dose_0400, dose_1000, dose_1600, dose_2200 = schedule
                cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
                cleaned_data.update(
                    {
                        "flucyt_dose_rx": 4000,
                        "flucyt_dose_0400": dose_0400,
                        "flucyt_dose_1000": dose_1000,
                        "flucyt_dose_1600": dose_1600,
                        "flucyt_dose_2200": dose_2200,
                    }
                )
                form_validator = StudyMedicationFollowupFormValidator(
                    cleaned_data=cleaned_data
                )
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    #
    def test_sum_individual_flucyt_doses_not_eq_flucyt_dose_rx_raises(self):
        self.mock_is_baseline.return_value = False
        dose_schedules = (
            (0, 0, 0, 0),
            (1, 1, 1, 1),
            (1000, 1000, 1000, 999),
            (1001, 1000, 1000, 1000),
            (0, 1000, 1000, 0),
        )
        for schedule in dose_schedules:
            with self.subTest(schedule=schedule):
                dose_0400, dose_1000, dose_1600, dose_2200 = schedule
                cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
                cleaned_data.update(
                    {
                        "flucyt_dose_rx": 4000,
                        "flucyt_dose_0400": dose_0400,
                        "flucyt_dose_1000": dose_1000,
                        "flucyt_dose_1600": dose_1600,
                        "flucyt_dose_2200": dose_2200,
                    }
                )
                form_validator = StudyMedicationFollowupFormValidator(
                    cleaned_data=cleaned_data
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("flucyt_dose_0400", cm.exception.error_dict)
                self.assertIn("flucyt_dose_1000", cm.exception.error_dict)
                self.assertIn("flucyt_dose_1600", cm.exception.error_dict)
                self.assertIn("flucyt_dose_2200", cm.exception.error_dict)
                expected_msg = (
                    "Invalid. "
                    "Expected sum of individual doses to match prescribed flucytosine "
                    "dose (4000 mg/d)."
                )
                self.assertIn(
                    expected_msg, str(cm.exception.error_dict.get("flucyt_dose_0400"))
                )
                self.assertIn(
                    expected_msg, str(cm.exception.error_dict.get("flucyt_dose_1000"))
                )
                self.assertIn(
                    expected_msg, str(cm.exception.error_dict.get("flucyt_dose_1600"))
                )
                self.assertIn(
                    expected_msg, str(cm.exception.error_dict.get("flucyt_dose_2200"))
                )

    def test_flucyt_notes_not_required_if_flucyt_modified_na(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY03, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucyt_modified": NOT_APPLICABLE,
                "flucyt_dose_datetime": None,
                "flucyt_dose_rx": None,
                "flucyt_dose_0400": None,
                "flucyt_dose_1000": None,
                "flucyt_dose_1600": None,
                "flucyt_dose_2200": None,
                "flucyt_notes": "Some flucyt notes here",
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucyt_notes", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("flucyt_notes")),
        )

    def test_flucyt_notes_with_d14_flucyt_dose_0_ok(self):
        self.mock_is_baseline.return_value = False
        cleaned_data = self.get_cleaned_data(visit_code=DAY14, visit_code_sequence=0)
        cleaned_data.update(
            {
                "flucyt_modified": YES,
                "flucyt_dose_rx": 0,
                "flucyt_dose_0400": 0,
                "flucyt_dose_1000": 0,
                "flucyt_dose_1600": 0,
                "flucyt_dose_2200": 0,
                "flucyt_notes": "Some other flucyt notes here",
            }
        )
        form_validator = StudyMedicationFollowupFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")
