from datetime import datetime
from decimal import Decimal
from typing import Optional

from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django_mock_queries.query import MockModel
from edc_utils import get_utcnow
from edc_visit_schedule.constants import (
    DAY01,
    DAY03,
    DAY09,
    DAY14,
    WEEK04,
    WEEK10,
    WEEK16,
    WEEK24,
)


class TestCaseMixin(TestCase):
    visit_schedule = [
        DAY01,
        DAY03,
        DAY09,
        DAY14,
        WEEK04,
        WEEK10,
        WEEK16,
        WEEK24,
    ]

    def setUp(self) -> None:
        """Setup appointment and subject_visit Mock models"""
        self.screening_datetime = get_utcnow() - relativedelta(years=1)
        self.consent_datetime = self.screening_datetime
        self.subject_identifier = "12345"
        # appointment
        self.appointment = MockModel(
            mock_name="Appointment",
            subject_identifier=self.subject_identifier,
            appt_datetime=self.consent_datetime,
            visit_code=DAY01,
            visit_code_sequence=0,
            visit_schedule_name="visit_schedule",
            schedule_name="schedule_name",
            timepoint=Decimal("0.0"),
        )

        # subject_visit
        self.subject_visit = MockModel(
            mock_name="SubjectVisit",
            subject_identifier=self.subject_identifier,
            report_datetime=self.consent_datetime,
            visit_code=DAY01,
            visit_code_sequence=0,
            appointment=self.appointment,
            signsandsymptoms=None,
            visit_schedule_name=self.appointment.visit_schedule,
            schedule_name=self.appointment.schedule_name,
            timepoint=self.appointment.timepoint,
        )

    def get_cleaned_data(
        self,
        visit_code: Optional[str] = None,
        report_datetime: Optional[datetime] = None,
        visit_code_sequence: Optional[int] = None,
    ) -> dict:
        """Returns dict of subject_visit and report_datetime.

        Updates visit_code and report_datetime if provided.
        """
        visit_code = visit_code or DAY01
        visit_code_sequence = visit_code_sequence or 0
        report_datetime = report_datetime or self.consent_datetime
        self.appointment.visit_code = visit_code
        self.appointment.visit_code_sequence = visit_code_sequence
        self.appointment.report_datetime = report_datetime
        self.appointment.visit_schedule_name = "visit_schedule"
        self.appointment.schedule_name = "schedule"
        self.subject_visit.appointment = self.appointment
        self.subject_visit.visit_code = visit_code
        self.subject_visit.visit_code_sequence = visit_code_sequence
        self.subject_visit.report_datetime = report_datetime
        self.subject_visit.visit_schedule_name = "visit_schedule"
        self.subject_visit.schedule_name = "schedule"
        return dict(
            subject_visit=self.subject_visit,
            report_datetime=report_datetime,
        )
