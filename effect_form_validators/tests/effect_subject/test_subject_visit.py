from typing import Optional

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.test import TestCase, tag
from edc_constants.constants import ALIVE, IN_PERSON, NO, NOT_APPLICABLE, PATIENT, YES
from edc_visit_schedule.constants import DAY01, DAY14
from edc_visit_tracking.constants import SCHEDULED

from effect_form_validators.effect_subject import SubjectVisitFormValidator as Base

from ..mixins import FormValidatorTestMixin, TestCaseMixin


class SubjectFormValidator(FormValidatorTestMixin, Base):
    pass


class TestVitalSignsFormValidator(TestCaseMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

    def get_cleaned_data(self, visit_code: Optional[str] = None, **kwargs) -> dict:
        cleaned_data = super().get_cleaned_data(visit_code=visit_code, **kwargs)
        cleaned_data.update(
            {
                "appointment": self.subject_visit.appointment,
                # "report_datetime": self.subject_visit.report_datetime,
                "reason": SCHEDULED,
                "reason_unscheduled": NOT_APPLICABLE,
                "reason_unscheduled_other": "",
                "assessment_type": IN_PERSON,
                "assessment_type_other": "",
                "assessment_who": PATIENT,
                "assessment_who_other": "",
                "info_source": PATIENT,
                "info_source_other": "",
                "survival_status": ALIVE,
                "last_alive_date": "",
                "hospitalized": NO,
                "comments": "",
            }
        )
        return cleaned_data

    @tag("sv1")
    def test_valid_in_person_sv_data_ok(self):
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        form_validator = SubjectFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    @tag("1")
    def test_baseline_with_valid_data_ok(self):
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_d14_with_valid_data_ok(self):
        cleaned_data = self.get_cleaned_data(
            visit_code=DAY14,
            report_datetime=self.consent_datetime + relativedelta(days=14),
        )
        form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_reportable_as_ae_not_applicable_at_baseline(self):
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        for response in [YES, NO]:
            with self.subTest(reportable_as_ae=response):
                cleaned_data.update(reportable_as_ae=response)
                form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("reportable_as_ae", cm.exception.error_dict)
                self.assertIn(
                    "Not applicable at baseline",
                    str(cm.exception.error_dict.get("reportable_as_ae")),
                )

    def test_patient_admitted_not_applicable_at_baseline(self):
        cleaned_data = self.get_cleaned_data(visit_code=DAY01)
        for response in [YES, NO]:
            with self.subTest(patient_admitted=response):
                cleaned_data.update(patient_admitted=response)
                form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("patient_admitted", cm.exception.error_dict)
                self.assertIn(
                    "Not applicable at baseline",
                    str(cm.exception.error_dict.get("patient_admitted")),
                )

    def test_reportable_as_ae_is_applicable_if_not_baseline(self):
        cleaned_data = self.get_cleaned_data(
            visit_code=DAY14,
            report_datetime=self.consent_datetime + relativedelta(days=14),
        )
        cleaned_data.update(reportable_as_ae=NOT_APPLICABLE)

        form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("reportable_as_ae", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable",
            str(cm.exception.error_dict.get("reportable_as_ae")),
        )

        for response in [YES, NO]:
            with self.subTest(reportable_as_ae=response):
                cleaned_data.update(reportable_as_ae=response)
                form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_patient_admitted_is_applicable_if_not_baseline(self):
        cleaned_data = self.get_cleaned_data(
            visit_code=DAY14,
            report_datetime=self.consent_datetime + relativedelta(days=14),
        )
        cleaned_data.update(patient_admitted=NOT_APPLICABLE)

        form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("patient_admitted", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable",
            str(cm.exception.error_dict.get("patient_admitted")),
        )

        for response in [YES, NO]:
            with self.subTest(patient_admitted=response):
                cleaned_data.update(patient_admitted=response)
                form_validator = VitalSignsFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")
