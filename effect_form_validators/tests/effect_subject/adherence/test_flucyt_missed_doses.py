from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from edc_constants.constants import CONTROL, INTERVENTION, REFUSED
from edc_utils import get_utcnow

from effect_form_validators.effect_subject import FlucytMissedDosesFormValidator

from ...mixins import TestCaseMixin
from ...mock_models import AdherenceMockModel, FlucytMissedDosesMockModel


class TestFlucytMissedDosesFormValidators(TestCaseMixin, TestCase):
    """See also: TestConcreteMissedDosesFormValidators for further
    missed doses form validation tests.
    """

    def setUp(self) -> None:
        super().setUp()

        assignment_patcher = patch(
            "effect_form_validators.effect_subject.adherence."
            "flucyt_missed_doses_form_validator.get_assignment_for_subject"
        )
        self.addCleanup(assignment_patcher.stop)
        self.mock_get_assignment_for_subject = assignment_patcher.start()
        self.mock_get_assignment_for_subject.return_value = INTERVENTION

        assignment_descr_patcher = patch(
            "effect_form_validators.effect_subject.adherence."
            "flucyt_missed_doses_form_validator.get_assignment_description_for_subject"
        )
        self.addCleanup(assignment_descr_patcher.stop)
        self.mock_get_assignment_description_for_subject = assignment_descr_patcher.start()
        self.mock_get_assignment_description_for_subject.return_value = (
            "2 weeks fluconazole plus flucytosine"
        )

    def get_cleaned_data(self, **kwargs) -> dict:
        if "report_datetime" not in kwargs:
            kwargs["report_datetime"] = get_utcnow()
        cleaned_data = super().get_cleaned_data(**kwargs)
        cleaned_data.update(
            {
                "adherence": AdherenceMockModel(subject_identifier=self.subject_identifier),
                "day_missed": None,
                "doses_missed": None,
                "missed_reason": "",
                "missed_reason_other": "",
            }
        )
        return cleaned_data

    def test_cleaned_data_ok(self):
        cleaned_data = self.get_cleaned_data()
        form_validator = FlucytMissedDosesFormValidator(
            cleaned_data=cleaned_data, model=FlucytMissedDosesMockModel
        )
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_in_range_missed_doses_ok(self):
        for day_missed in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]:
            for doses_missed in [1, 2, 3, 4]:
                with self.subTest(day_missed=day_missed, doses_missed=doses_missed):
                    cleaned_data = self.get_cleaned_data()
                    cleaned_data.update(
                        {
                            "day_missed": day_missed,
                            "doses_missed": doses_missed,
                            "missed_reason": REFUSED,
                            "missed_reason_other": "",
                        }
                    )
                    form_validator = FlucytMissedDosesFormValidator(
                        cleaned_data=cleaned_data, model=FlucytMissedDosesMockModel
                    )
                    try:
                        form_validator.validate()
                    except ValidationError as e:
                        self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_day_missed_not_required_if_on_control_arm(self):
        self.mock_get_assignment_for_subject.return_value = CONTROL
        self.mock_get_assignment_description_for_subject.return_value = (
            "2 weeks fluconazole alone"
        )
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "day_missed": 3,
                "doses_missed": 1,
                "missed_reason": REFUSED,
                "missed_reason_other": "",
            }
        )
        form_validator = FlucytMissedDosesFormValidator(
            cleaned_data=cleaned_data, model=FlucytMissedDosesMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("day_missed", cm.exception.error_dict)
        self.assertIn(
            "This field is not required. "
            "Participant is on control arm (2 weeks fluconazole alone).",
            str(cm.exception.error_dict.get("day_missed")),
        )

    def test_doses_missed_required_if_day_field_specified(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "day_missed": 3,
                "doses_missed": None,
                "missed_reason": REFUSED,
                "missed_reason_other": "",
            }
        )
        form_validator = FlucytMissedDosesFormValidator(
            cleaned_data=cleaned_data, model=FlucytMissedDosesMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("doses_missed", cm.exception.error_dict)
        self.assertIn(
            "This field is required",
            str(cm.exception.error_dict.get("doses_missed")),
        )

    def test_out_of_day_range_doses_missed_not_required(self):
        for day_missed in [-1, 0, 16, 20, 100]:
            with self.subTest(day_missed=day_missed):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "day_missed": day_missed,
                        "doses_missed": 1,
                        "missed_reason": REFUSED,
                        "missed_reason_other": "",
                    }
                )
                form_validator = FlucytMissedDosesFormValidator(
                    cleaned_data=cleaned_data, model=FlucytMissedDosesMockModel
                )
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("doses_missed", cm.exception.error_dict)
                self.assertIn(
                    "This field is not required.",
                    str(cm.exception.error_dict.get("doses_missed")),
                )

    def test_doses_missed_not_required_if_day_field_not_specified(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "day_missed": None,
                "doses_missed": 2,
                "missed_reason": "",
                "missed_reason_other": "",
            }
        )
        form_validator = FlucytMissedDosesFormValidator(
            cleaned_data=cleaned_data, model=FlucytMissedDosesMockModel
        )
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("doses_missed", cm.exception.error_dict)
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("doses_missed")),
        )
