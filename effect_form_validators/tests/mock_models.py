from django_mock_queries.query import MockModel


class AdherenceMockModel(MockModel):
    def __init__(self, subject_identifier: str, *args, **kwargs):
        kwargs["mock_name"] = "Adherence"
        super().__init__(*args, **kwargs)
        self._meta.label_lower = "effect_subject.adherence"
        self.subject_identifier = subject_identifier


class FlucytMissedDosesMockModel(MockModel):
    def __init__(self, *args, **kwargs):
        kwargs["mock_name"] = "FlucytMissedDoses"
        super().__init__(*args, **kwargs)
        self._meta.label_lower = "effect_subject.flucytmisseddoses"
