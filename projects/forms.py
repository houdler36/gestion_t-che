from django import forms

from projects.models import Activity, Project, SubActivity
from accounts.models import User


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name',
            'description',
            'start_date',
            'end_date',
            'status',
            'members',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du projet'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description...'}
            ),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'members': forms.SelectMultiple(
                attrs={'class': 'form-select', 'style': 'height: 120px;'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['members'].queryset = User.objects.filter(is_active=True)
        self.fields['members'].help_text = (
            'Maintenez Ctrl (ou Cmd sur Mac) pour sélectionner plusieurs membres'
        )


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['code', 'name', 'description', 'responsible', 'start_date', 'end_date']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Code de l'activité"}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom de l'activité"}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description...'}
            ),
            'responsible': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsible'].queryset = project.members.all()
        self.fields['responsible'].empty_label = 'Choisir un responsable'


class SubActivityForm(forms.ModelForm):
    class Meta:
        model = SubActivity
        fields = ['code', 'name', 'description', 'assigned_to', 'status']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code de la sous-activité'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom de la sous-activité"}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description...'}
            ),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


    def __init__(self, activity, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = activity.project.members.all()
        self.fields['assigned_to'].empty_label = 'Choisir un membre'

