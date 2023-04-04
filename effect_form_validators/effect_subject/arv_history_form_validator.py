from edc_constants.constants import DEFAULTED, NO, NOT_APPLICABLE, YES
from edc_crf.crf_form_validator import CrfFormValidator
from edc_form_validators import INVALID_ERROR
from edc_screening.utils import get_subject_screening_model_cls


class ArvHistoryFormValidator(CrfFormValidator):
    @property
    def subject_screening(self):
        return get_subject_screening_model_cls().objects.get(
            subject_identifier=self.subject_identifier
        )

    def clean(self) -> None:
        self.validate_date_against_report_datetime("hiv_dx_date")
        self.validate_hiv_dx_date_against_screening_cd4_date()

        # ARV treatment and monitoring
        condition = (
            self.cleaned_data.get("on_art_at_crag")
            and self.cleaned_data.get("ever_on_art")
            and (
                self.cleaned_data.get("on_art_at_crag") == YES
                or self.cleaned_data.get("ever_on_art") == YES
            )
        )
        # TODO: if YES, on ART prior to CrAg, compare to CrAg date??
        self.required_if_true(condition, field_required="initial_art_date")

        self.validate_date_against_report_datetime("initial_art_date")

        self.applicable_if_true(
            self.cleaned_data.get("initial_art_date"),
            field_applicable="initial_art_date_estimated",
        )

        self.m2m_applicable_if_true(
            self.cleaned_data.get("initial_art_date"), m2m_field="initial_art_regimen"
        )

        self.m2m_single_selection_if(NOT_APPLICABLE, m2m_field="initial_art_regimen")

        self.m2m_other_specify(
            m2m_field="initial_art_regimen", field_other="initial_art_regimen_other"
        )

        self.applicable_if_true(
            self.cleaned_data.get("initial_art_date"),
            field_applicable="has_switched_art_regimen",
        )

        self.required_if(
            YES, field="has_switched_art_regimen", field_required="current_art_date"
        )

        self.date_not_before(
            "initial_art_date",
            "current_art_date",
            "Invalid. Cannot be before ART start date",
            message_on_field="current_art_date",
        )

        self.date_not_equal(
            "current_art_date",
            "initial_art_date",
            "Invalid. Cannot be equal to the ART start date",
            message_on_field="current_art_date",
        )

        self.validate_date_against_report_datetime("current_art_date")

        self.applicable_if(
            YES,
            field="has_switched_art_regimen",
            field_applicable="current_art_date_estimated",
        )

        self.m2m_applicable_if_true(
            self.cleaned_data.get("current_art_date"), m2m_field="current_art_regimen"
        )

        self.m2m_single_selection_if(NOT_APPLICABLE, m2m_field="current_art_regimen")

        self.m2m_other_specify(
            m2m_field="current_art_regimen", field_other="current_art_regimen_other"
        )

        self.validate_art_adherence()

        # art decision
        self.applicable_if(NO, field="has_defaulted", field_applicable="art_decision")

        # vl
        self.required_if(YES, field="has_viral_load", field_required="viral_load_result")
        self.required_if(YES, field="has_viral_load", field_required="viral_load_date")
        self.applicable_if(
            YES, field="has_viral_load", field_applicable="viral_load_date_estimated"
        )
        self.validate_date_against_report_datetime("viral_load_date")

        # self.date_not_before(
        #     "hiv_diagnosis_date",
        #     "viral_load_date",
        #     "Invalid. Cannot be before HIV diagnosis date.",
        # )

        self.validate_cd4_date()

        self.validate_cd4_against_screening_cd4_data()

    # self.required_if(
    #     YES, field="has_previous_arv_regimen", field_required="previous_arv_regimen"
    # )
    #
    # if self.cleaned_data.get("has_previous_arv_regimen") == NO:
    #     self.date_equal(
    #         "initial_art_date",
    #         "current_art_regimen_start_date",
    #         "Invalid. Expected current regimen date to equal initiation date.",
    #     )
    #
    # self.required_if(
    #     YES, field="has_previous_arv_regimen", field_required="previous_arv_regimen"
    # )
    #
    # self.required_if(
    #     OTHER,
    #     field="previous_arv_regimen",
    #     field_required="other_previous_arv_regimen",
    # )

    def validate_hiv_dx_date_against_screening_cd4_date(self):
        if (
            self.cleaned_data.get("hiv_dx_date")
            and self.cleaned_data.get("hiv_dx_date") > self.subject_screening.cd4_date
        ):
            self.raise_validation_error(
                {
                    "hiv_dx_date": (
                        "Invalid. Cannot be after screening CD4 date "
                        f"({self.subject_screening.cd4_date})."
                    )
                },
                INVALID_ERROR,
            )

    def validate_art_adherence(self):
        # defaulted
        self.applicable_if_true(
            self.cleaned_data.get("initial_art_date"),
            field_applicable="has_defaulted",
        )

        self.required_if(YES, field="has_defaulted", field_required="defaulted_date")

        self.date_not_before(
            "initial_art_date",
            "defaulted_date",
            "Invalid. Cannot be before initial ART start date",
            message_on_field="defaulted_date",
        )

        self.date_not_equal(
            "initial_art_date",
            "defaulted_date",
            "Invalid. Cannot be equal to the current ART start date",
            message_on_field="defaulted_date",
        )

        self.date_not_before(
            "current_art_date",
            "defaulted_date",
            "Invalid. Cannot be before current ART start date",
            message_on_field="defaulted_date",
        )

        self.date_not_equal(
            "current_art_date",
            "defaulted_date",
            "Invalid. Cannot be equal to the current ART start date",
            message_on_field="defaulted_date",
        )

        self.applicable_if_true(
            self.cleaned_data.get("defaulted_date"),
            field_applicable="defaulted_date_estimated",
        )

        # adherent
        self.applicable_if(YES, NO, field="has_defaulted", field_applicable="is_adherent")
        if (
            self.cleaned_data.get("has_defaulted") != YES
            and self.cleaned_data.get("is_adherent") == DEFAULTED
        ):
            self.raise_validation_error(
                {
                    "is_adherent": (
                        "Invalid. "
                        "Participant not reported as defaulted from their "
                        "current ART regimen."
                    )
                },
                INVALID_ERROR,
            )
        elif (
            self.cleaned_data.get("has_defaulted") == YES
            and self.cleaned_data.get("is_adherent") != DEFAULTED
        ):
            self.raise_validation_error(
                {
                    "is_adherent": (
                        "Invalid. "
                        "Expected DEFAULTED. Participant reported as defaulted "
                        "from their current ART regimen."
                    )
                },
                INVALID_ERROR,
            )

        self.required_if(
            NO,
            field="is_adherent",
            field_required="art_doses_missed",
            field_required_evaluate_as_int=True,
        )

    def validate_cd4_date(self):
        self.validate_date_against_report_datetime("cd4_date")
        self.date_not_before(
            "hiv_dx_date",
            "cd4_date",
            "Invalid. Cannot be before 'HIV diagnosis first known' date",
            message_on_field="cd4_date",
        )

    def validate_cd4_against_screening_cd4_data(self):
        arv_history_cd4_value = self.cleaned_data.get("cd4_value")
        arv_history_cd4_date = self.cleaned_data.get("cd4_date")
        if (
            arv_history_cd4_value
            and arv_history_cd4_date
            and arv_history_cd4_date == self.subject_screening.cd4_date
            and arv_history_cd4_value != self.subject_screening.cd4_value
        ):
            self.raise_validation_error(
                {
                    "cd4_value": (
                        "Invalid. Cannot differ from screening CD4 count "
                        f"({self.subject_screening.cd4_value}) if collected on same date."
                    )
                },
                INVALID_ERROR,
            )

        if arv_history_cd4_date and arv_history_cd4_date < self.subject_screening.cd4_date:
            self.raise_validation_error(
                {
                    "cd4_date": (
                        "Invalid. Cannot be before screening CD4 date "
                        f"({self.subject_screening.cd4_date})."
                    )
                },
                INVALID_ERROR,
            )
