from django import forms


# TODO: Remove/switch to edc-vitals after next edc release (>=0.3.94)
class BloodPressureFormValidatorMixin:
    @staticmethod
    def raise_on_systolic_lt_diastolic_bp(
        sys_field: str = None, dia_field: str = None, **kwargs
    ) -> None:
        """Raise if systolic BP is < diastolic BP."""
        sys_field = sys_field or "sys_blood_pressure"
        dia_field = dia_field or "dia_blood_pressure"
        sys_response = kwargs.get(sys_field)
        dia_response = kwargs.get(dia_field)
        if sys_response and dia_response:
            if sys_response < dia_response:
                raise forms.ValidationError(
                    {dia_field: "Invalid. Diastolic must be less than systolic."}
                )
