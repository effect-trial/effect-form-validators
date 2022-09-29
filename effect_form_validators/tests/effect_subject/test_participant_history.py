from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.test import TestCase
from django_mock_queries.query import MockModel, MockSet
from edc_constants.constants import NO, NOT_APPLICABLE, OTHER, YES

from effect_form_validators.effect_subject import (
    ParticipantHistoryFormValidator as Base,
)

from ..mixins import FormValidatorTestMixin, TestCaseMixin


class ParticipantHistoryMockModel(MockModel):
    @classmethod
    def related_visit_model_attr(cls):
        return "subject_visit"


class ParticipantHistoryFormValidator(FormValidatorTestMixin, Base):
    pass


class TestParticipantHistoryFormValidator(TestCaseMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.medications_choice_na = MockModel(
            mock_name="Medication", name=NOT_APPLICABLE, display_name=NOT_APPLICABLE
        )
        self.medications_choice_tmp_smx = MockModel(
            mock_name="Medication", name="TMP-SMX", display_name="TMP-SMX"
        )
        self.medications_choice_steroids = MockModel(
            mock_name="Medication", name="steroids", display_name="steroids"
        )
        self.medications_choice_other = MockModel(
            mock_name="Medication", name=OTHER, display_name=OTHER
        )
        self.tb_treatments_choice_hrze = MockModel(
            mock_name="TbTreatments", name="HRZE", display_name="HRZE"
        )

    def get_cleaned_data(self, **kwargs) -> dict:
        cleaned_data = super().get_cleaned_data(**kwargs)
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": NO,
                "flucon_days": None,
                "flucon_dose": NOT_APPLICABLE,
                "flucon_dose_other": None,
                "flucon_dose_other_reason": "",
                "reported_neuro_abnormality": NO,
                "neuro_abnormality_details": "",
                "tb_prev_dx": NO,
                "tb_dx_date": None,
                "tb_dx_date_estimated": NOT_APPLICABLE,
                "tb_site": NOT_APPLICABLE,
                "on_tb_tx": NO,
                "tb_tx_type": NOT_APPLICABLE,
                "active_tb_tx": None,
                "previous_oi": NO,
                "previous_oi_name": "",
                "previous_oi_dx_date": None,
                "any_medications": NO,
                "specify_medications": MockSet(self.medications_choice_na),
                "specify_steroid_other": "",
                "specify_medications_other": "",
            }
        )
        return cleaned_data

    def test_cleaned_data_ok(self):
        cleaned_data = self.get_cleaned_data()
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucon_days_required_if_flucon_1w_prior_rando_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": YES,
                "flucon_days": None,
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_days", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucon_days")),
        )

        cleaned_data.update(
            {
                "flucon_days": 6,
                "flucon_dose": "1200_mg_d",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucon_days_not_required_if_flucon_1w_prior_rando_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": NO,
                "flucon_days": 2,
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_days", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("flucon_days")),
        )

    def test_flucon_dose_applicable_if_flucon_1w_prior_rando_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": YES,
                "flucon_days": 1,
                "flucon_dose": NOT_APPLICABLE,
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("flucon_dose")),
        )

        cleaned_data.update(
            {
                "flucon_dose": "800_mg_d",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucon_dose_not_applicable_if_flucon_1w_prior_rando_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": NO,
                "flucon_days": None,
                "flucon_dose": "800_mg_d",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose", cm.exception.error_dict)
        self.assertIn(
            "This field is not applicable.",
            str(cm.exception.error_dict.get("flucon_dose")),
        )

    def test_flucon_dose_other_required_if_flucon_dose_is_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": YES,
                "flucon_days": 7,
                "flucon_dose": OTHER,
                "flucon_dose_other": None,
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_other", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucon_dose_other")),
        )

        cleaned_data.update(
            {
                "flucon_dose_other": 400,
                "flucon_dose_other_reason": "reason for other dose",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucon_dose_other_not_required_if_flucon_dose_is_not_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": YES,
                "flucon_days": 1,
                "flucon_dose": "800_mg_d",
                "flucon_dose_other": 400,
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_other", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("flucon_dose_other")),
        )

    def test_flucon_dose_other_reason_required_if_flucon_dose_is_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": YES,
                "flucon_days": 7,
                "flucon_dose": OTHER,
                "flucon_dose_other": 400,
                "flucon_dose_other_reason": "",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_other_reason", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("flucon_dose_other_reason")),
        )

        cleaned_data.update(
            {
                "flucon_dose_other_reason": "reason for other dose",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_flucon_dose_other_reason_not_required_if_flucon_dose_is_not_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "flucon_1w_prior_rando": YES,
                "flucon_days": 1,
                "flucon_dose": "800_mg_d",
                "flucon_dose_other": None,
                "flucon_dose_other_reason": "Some other reason",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("flucon_dose_other_reason", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("flucon_dose_other_reason")),
        )

    def test_neuro_abnormality_details_required_if_reported_neuro_abnormality_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "reported_neuro_abnormality": YES,
                "neuro_abnormality_details": "",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("neuro_abnormality_details", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("neuro_abnormality_details")),
        )

        cleaned_data.update(
            {
                "neuro_abnormality_details": "Details of abnormality",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_neuro_abnormality_details_not_required_if_reported_neuro_abnormality_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "reported_neuro_abnormality": NO,
                "neuro_abnormality_details": "Details of abnormality",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("neuro_abnormality_details", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("neuro_abnormality_details")),
        )

    def test_tb_dx_date_required_if_prev_tb_dx_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "tb_prev_dx": YES,
                "tb_dx_date": None,
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("tb_dx_date", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("tb_dx_date")),
        )

        cleaned_data.update(
            {
                "tb_dx_date": self.consent_datetime.date() - relativedelta(years=1),
                "tb_dx_date_estimated": NO,
                "tb_site": "extra_pulmonary",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_tb_dx_date_not_required_if_prev_tb_dx_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "tb_prev_dx": NO,
                "tb_dx_date": self.consent_datetime.date() - relativedelta(years=1),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("tb_dx_date", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("tb_dx_date")),
        )

    def test_tb_dx_date_estimated_applicable_if_prev_tb_dx_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "tb_prev_dx": YES,
                "tb_dx_date": self.consent_datetime.date() - relativedelta(years=1),
                "tb_dx_date_estimated": NOT_APPLICABLE,
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("tb_dx_date_estimated", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("tb_dx_date_estimated")),
        )

        cleaned_data.update(
            {
                "tb_dx_date_estimated": YES,
                "tb_site": "pulmonary",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_tb_dx_date_estimated_not_applicable_if_prev_tb_dx_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "tb_prev_dx": NO,
                "tb_dx_date": None,
                "tb_dx_date_estimated": NO,
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("tb_dx_date_estimated", cm.exception.error_dict)
        self.assertIn(
            "This field is not applicable.",
            str(cm.exception.error_dict.get("tb_dx_date_estimated")),
        )

    def test_tb_site_applicable_if_prev_tb_dx_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "tb_prev_dx": YES,
                "tb_dx_date": self.consent_datetime.date() - relativedelta(years=1),
                "tb_dx_date_estimated": NO,
                "tb_site": NOT_APPLICABLE,
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("tb_site", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("tb_site")),
        )

        cleaned_data.update({"tb_site": "extra_pulmonary"})
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_tb_site_not_required_if_prev_tb_dx_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "tb_prev_dx": NO,
                "tb_dx_date": None,
                "tb_dx_date_estimated": NOT_APPLICABLE,
                "tb_site": "pulmonary",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("tb_site", cm.exception.error_dict)
        self.assertIn(
            "This field is not applicable.",
            str(cm.exception.error_dict.get("tb_site")),
        )

    def test_tb_tx_type_applicable_if_on_tb_tx_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "on_tb_tx": YES,
                "tb_tx_type": NOT_APPLICABLE,
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("tb_tx_type", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable.",
            str(cm.exception.error_dict.get("tb_tx_type")),
        )

        cleaned_data.update({"tb_tx_type": "ipt"})
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_tb_tx_type_not_applicable_if_on_tb_tx_no(self):
        for tx_type in ["active_tb", "latent_tb", "ipt"]:
            with self.subTest(tx_type=tx_type):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "on_tb_tx": NO,
                        "tb_tx_type": tx_type,
                    }
                )
                form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("tb_tx_type", cm.exception.error_dict)
                self.assertIn(
                    "This field is not applicable.",
                    str(cm.exception.error_dict.get("tb_tx_type")),
                )

                cleaned_data.update({"tb_tx_type": NOT_APPLICABLE})
                form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
                try:
                    form_validator.validate()
                except ValidationError as e:
                    self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_active_tb_with_tb_prev_dx_no_raises(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "tb_prev_dx": NO,
                "tb_dx_date": None,
                "tb_dx_date_estimated": NOT_APPLICABLE,
                "tb_site": NOT_APPLICABLE,
                "on_tb_tx": YES,
                "tb_tx_type": "active_tb",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("tb_tx_type", cm.exception.error_dict)
        self.assertIn(
            "Invalid. "
            "No previous diagnosis of Tuberculosis. "
            "Expected one of ['IPT', 'Not applicable'].",
            str(cm.exception.error_dict.get("tb_tx_type")),
        )

        cleaned_data.update({"tb_tx_type": "ipt"})
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_active_tb_with_tb_prev_dx_yes_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "tb_prev_dx": YES,
                "tb_dx_date": self.consent_datetime.date() - relativedelta(months=1),
                "tb_dx_date_estimated": NO,
                "tb_site": "pulmonary",
                "on_tb_tx": YES,
                "tb_tx_type": "active_tb",
                "active_tb_tx": MockSet(self.tb_treatments_choice_hrze),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_latent_tb_with_tb_prev_dx_no_raises(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "tb_prev_dx": NO,
                "tb_dx_date": None,
                "tb_dx_date_estimated": NOT_APPLICABLE,
                "tb_site": NOT_APPLICABLE,
                "on_tb_tx": YES,
                "tb_tx_type": "latent_tb",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("tb_tx_type", cm.exception.error_dict)
        self.assertIn(
            "Invalid. "
            "No previous diagnosis of Tuberculosis. "
            "Expected one of ['IPT', 'Not applicable'].",
            str(cm.exception.error_dict.get("tb_tx_type")),
        )

        cleaned_data.update({"tb_tx_type": "ipt"})
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_latent_tb_with_tb_prev_dx_yes_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "tb_prev_dx": YES,
                "tb_dx_date": self.consent_datetime.date() - relativedelta(months=1),
                "tb_dx_date_estimated": NO,
                "tb_site": "pulmonary",
                "on_tb_tx": YES,
                "tb_tx_type": "latent_tb",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_ipt_with_tb_prev_dx_yes_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "tb_prev_dx": YES,
                "tb_dx_date": self.consent_datetime.date() - relativedelta(months=1),
                "tb_dx_date_estimated": NO,
                "tb_site": "pulmonary",
                "on_tb_tx": YES,
                "tb_tx_type": "ipt",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_ipt_with_tb_prev_dx_no_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "tb_prev_dx": NO,
                "tb_dx_date": None,
                "tb_dx_date_estimated": NOT_APPLICABLE,
                "tb_site": NOT_APPLICABLE,
                "on_tb_tx": YES,
                "tb_tx_type": "ipt",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_active_tb_tx_required_if_tb_tx_type_is_active_tb(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "tb_prev_dx": YES,
                "tb_dx_date": self.consent_datetime.date() - relativedelta(months=1),
                "tb_dx_date_estimated": NO,
                "tb_site": "pulmonary",
                "on_tb_tx": YES,
                "tb_tx_type": "active_tb",
                "active_tb_tx": MockSet(),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("active_tb_tx", cm.exception.error_dict)
        self.assertIn(
            "This field is required",
            str(cm.exception.error_dict.get("active_tb_tx")),
        )

        cleaned_data.update({"active_tb_tx": MockSet(self.tb_treatments_choice_hrze)})
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_active_tb_tx_not_required_if_tb_tx_type_is_not_active_tb(self):
        for tx_type in ["latent_tb", "ipt"]:
            with self.subTest(tx_type=tx_type):
                cleaned_data = self.get_cleaned_data()
                cleaned_data.update(
                    {
                        "tb_prev_dx": YES,
                        "tb_dx_date": self.consent_datetime.date() - relativedelta(months=1),
                        "tb_dx_date_estimated": NO,
                        "tb_site": "pulmonary",
                        "on_tb_tx": YES,
                        "tb_tx_type": tx_type,
                        "active_tb_tx": MockSet(self.tb_treatments_choice_hrze),
                    }
                )
                form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
                with self.assertRaises(ValidationError) as cm:
                    form_validator.validate()
                self.assertIn("active_tb_tx", cm.exception.error_dict)
                self.assertIn(
                    "This field is not required",
                    str(cm.exception.error_dict.get("active_tb_tx")),
                )

        cleaned_data.update({"active_tb_tx": None})
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_active_tb_tx_not_required_if_on_tb_tx_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "on_tb_tx": NO,
                "tb_tx_type": NOT_APPLICABLE,
                "active_tb_tx": MockSet(self.tb_treatments_choice_hrze),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("active_tb_tx", cm.exception.error_dict)
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("active_tb_tx")),
        )

        cleaned_data.update({"active_tb_tx": None})
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_previous_oi_name_required_if_previous_oi_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "previous_oi": YES,
                "previous_oi_name": "",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("previous_oi_name", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("previous_oi_name")),
        )

        cleaned_data.update(
            {
                "previous_oi_name": "Prev OI",
                "previous_oi_date": (
                    cleaned_data.get("report_datetime").date() - relativedelta(months=3)
                ),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_previous_oi_name_not_required_if_previous_oi_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "previous_oi": NO,
                "previous_oi_name": "Prev OI",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("previous_oi_name", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("previous_oi_name")),
        )

    def test_previous_oi_date_required_if_previous_oi_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "previous_oi": YES,
                "previous_oi_name": "Prev OI",
                "previous_oi_date": None,
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("previous_oi_date", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("previous_oi_date")),
        )

        cleaned_data.update(
            {
                "previous_oi_date": (
                    cleaned_data.get("report_datetime").date() - relativedelta(months=3)
                ),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_previous_oi_date_not_required_if_previous_oi_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "previous_oi": NO,
                "previous_oi_date": (
                    cleaned_data.get("report_datetime").date() - relativedelta(months=3)
                ),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("previous_oi_date", cm.exception.error_dict)
        self.assertIn(
            "This field is not required.",
            str(cm.exception.error_dict.get("previous_oi_date")),
        )

    def test_previous_oi_date_after_report_date_raises(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "previous_oi": YES,
                "previous_oi_name": "Prev OI",
                "previous_oi_date": (
                    cleaned_data.get("report_datetime").date() + relativedelta(days=1)
                ),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("previous_oi_date", cm.exception.error_dict)
        self.assertIn(
            "Cannot be after report datetime",
            str(cm.exception.error_dict.get("previous_oi_date")),
        )

    def test_previous_oi_date_on_report_date_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "previous_oi": YES,
                "previous_oi_name": "Prev OI",
                "previous_oi_date": cleaned_data.get("report_datetime").date(),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_previous_oi_date_before_report_date_ok(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "previous_oi": YES,
                "previous_oi_name": "Prev OI",
                "previous_oi_date": (
                    cleaned_data.get("report_datetime").date() - relativedelta(days=1)
                ),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_specify_medications_applicable_if_any_medications_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "any_medications": YES,
                "specify_medications": MockSet(self.medications_choice_na),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("specify_medications", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable",
            str(cm.exception.error_dict.get("specify_medications")),
        )

        cleaned_data.update(
            {
                "specify_medications": MockSet(self.medications_choice_tmp_smx),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_specify_medications_including_not_applicable_raises_if_any_medications_yes(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "any_medications": YES,
                "specify_medications": MockSet(
                    self.medications_choice_tmp_smx, self.medications_choice_na
                ),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("specify_medications", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable",
            str(cm.exception.error_dict.get("specify_medications")),
        )

        cleaned_data.update(
            {
                "specify_medications": MockSet(self.medications_choice_na),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("specify_medications", cm.exception.error_dict)
        self.assertIn(
            "This field is applicable",
            str(cm.exception.error_dict.get("specify_medications")),
        )

        cleaned_data.update(
            {
                "specify_medications": MockSet(self.medications_choice_tmp_smx),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_specify_medications_not_applicable_if_any_medications_no(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "any_medications": NO,
                "specify_medications": MockSet(self.medications_choice_tmp_smx),
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("specify_medications", cm.exception.error_dict)
        self.assertIn(
            "This field is not applicable",
            str(cm.exception.error_dict.get("specify_medications")),
        )

    def test_specify_steroid_other_required_if_specify_medications_includes_steroids(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "any_medications": YES,
                "specify_medications": MockSet(
                    self.medications_choice_tmp_smx,
                    self.medications_choice_steroids,
                ),
                "specify_steroid_other": "",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("specify_steroid_other", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("specify_steroid_other")),
        )

        cleaned_data.update(
            {
                "specify_steroid_other": "Other steroid",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_specify_steroid_other_not_required_if_specify_medications_excludes_steroids(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "any_medications": YES,
                "specify_medications": MockSet(self.medications_choice_tmp_smx),
                "specify_steroid_other": "Some other steroid",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("specify_steroid_other", cm.exception.error_dict)
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("specify_steroid_other")),
        )

        cleaned_data.update(
            {
                "any_medications": NO,
                "specify_medications": MockSet(self.medications_choice_na),
                "specify_steroid_other": "Some other steroid",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("specify_steroid_other", cm.exception.error_dict)
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("specify_steroid_other")),
        )

    def test_specify_medications_other_required_if_specify_medications_includes_other(self):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "any_medications": YES,
                "specify_medications": MockSet(
                    self.medications_choice_tmp_smx,
                    self.medications_choice_other,
                ),
                "specify_medications_other": "",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("specify_medications_other", cm.exception.error_dict)
        self.assertIn(
            "This field is required.",
            str(cm.exception.error_dict.get("specify_medications_other")),
        )

        cleaned_data.update(
            {
                "specify_medications_other": "Other medication",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        try:
            form_validator.validate()
        except ValidationError as e:
            self.fail(f"ValidationError unexpectedly raised. Got {e}")

    def test_specify_medications_other_not_required_if_specify_medications_excludes_other(
        self,
    ):
        cleaned_data = self.get_cleaned_data()
        cleaned_data.update(
            {
                "any_medications": YES,
                "specify_medications": MockSet(self.medications_choice_tmp_smx),
                "specify_medications_other": "Other medication",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("specify_medications_other", cm.exception.error_dict)
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("specify_medications_other")),
        )

        cleaned_data.update(
            {
                "any_medications": NO,
                "specify_medications": MockSet(self.medications_choice_na),
                "specify_medications_other": "Other medication",
            }
        )
        form_validator = ParticipantHistoryFormValidator(cleaned_data=cleaned_data)
        with self.assertRaises(ValidationError) as cm:
            form_validator.validate()
        self.assertIn("specify_medications_other", cm.exception.error_dict)
        self.assertIn(
            "This field is not required",
            str(cm.exception.error_dict.get("specify_medications_other")),
        )
