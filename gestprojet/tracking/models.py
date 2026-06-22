from django import forms
from .models import DailyLog

class DailyLogForm(forms.ModelForm):

    class Meta:
        model = DailyLog
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():

            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    "class": "form-select"
                })

            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": field.label
                })

            else:
                field.widget.attrs.update({
                    "class": "form-control",
                    "placeholder": field.label
                })