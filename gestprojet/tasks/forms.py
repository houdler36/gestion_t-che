from django import forms

from projects.models import Activity, SubActivity
from tasks.models import Task


class TaskForm(forms.ModelForm):
    """Formulaire Task avec champ dépendant Projet -> Activité -> Sous-activité."""

    # Champ non présent dans le modèle Task (on le sert pour piloter sub_activity)
    activity = forms.ModelChoiceField(
        queryset=Activity.objects.none(),
        required=False,
        empty_label="---------",
        help_text="Activité liée au projet (optionnel)",
    )

    class Meta:
        model = Task
        fields = [
            "name",
            "description",
            "project",
            "activity",
            "sub_activity",
            "assigned_to",
            "priority",
            "due_date",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # En édition, déduire activity/project depuis sub_activity (sinon le filtrage
        # de sub_activity peut masquer la valeur existante).
        if getattr(self.instance, "pk", None) and getattr(self.instance, "sub_activity_id", None):
            try:
                activity_id = self.instance.sub_activity.activity_id
                if activity_id and not self.initial.get("activity"):
                    self.initial["activity"] = activity_id

                project_id = self.instance.sub_activity.activity.project_id
                if project_id and not self.initial.get("project"):
                    self.initial["project"] = project_id
            except Exception:
                pass

        user = getattr(self.request, "user", None) if hasattr(self, "request") else None
        role = getattr(user, "role", None)


        # Base querysets
        activity_qs = Activity.objects.all()
        sub_activity_qs = SubActivity.objects.none()

        if role == "PM" and user is not None:
            user_projects = user.projects.all()
            activity_qs = activity_qs.filter(project__in=user_projects)

        selected_project = self.data.get("project") if self.is_bound else self.initial.get("project")
        selected_activity = self.data.get("activity") if self.is_bound else self.initial.get("activity")

        # activity queryset
        if selected_project:
            activity_qs = activity_qs.filter(project_id=selected_project)

        self.fields["activity"].queryset = activity_qs

        # sub_activity queryset
        if selected_activity:
            sub_activity_qs = SubActivity.objects.filter(activity_id=selected_activity)
            if role == "PM" and user is not None:
                sub_activity_qs = sub_activity_qs.filter(activity__project__in=user.projects.all())
        elif selected_project:
            # utile en édition si aucune activité n'a été envoyée
            sub_activity_qs = SubActivity.objects.filter(activity__project_id=selected_project)
            if role == "PM" and user is not None:
                sub_activity_qs = sub_activity_qs.filter(activity__project__in=user.projects.all())

        # ✅ En édition, garantir que la sous-activité de l'instance est toujours présente
        # dans le queryset, sinon Django ne peut pas la pré-sélectionner (option absente).
        if getattr(self.instance, "pk", None) and getattr(self.instance, "sub_activity_id", None):
            sub_activity_qs = sub_activity_qs | SubActivity.objects.filter(pk=self.instance.sub_activity_id)

        self.fields["sub_activity"].queryset = sub_activity_qs

        try:
            self.fields["sub_activity"].empty_label = "---------"
        except Exception:
            pass

        # Widgets (compat style existant)
        self.fields["project"].widget.attrs.update({"class": "form-select"})
        self.fields["activity"].widget.attrs.update({"class": "form-select"})
        self.fields["sub_activity"].widget.attrs.update({"class": "form-select"})
        self.fields["name"].widget.attrs.update({"class": "form-control"})
        self.fields["description"].widget.attrs.update({"class": "form-control"})
        self.fields["assigned_to"].widget.attrs.update({"class": "form-select"})
        self.fields["priority"].widget.attrs.update({"class": "form-select"})
        # Force le rendu HTML 5 calendrier (input type="date")
        # afin d'éviter que Django ne rende un champ texte sur certains navigateurs.
        self.fields["due_date"].widget.attrs.update({"class": "form-control", "type": "date"})
        self.fields["status"].widget.attrs.update({"class": "form-select"})

    def clean(self):
        cleaned = super().clean()
        activity = cleaned.get("activity")
        sub_activity = cleaned.get("sub_activity")

        # Sécurité minimale : si sub_activity est sélectionnée, elle doit appartenir à l'activité.
        if activity is not None and sub_activity is not None:
            if sub_activity.activity_id != activity.id:
                self.add_error(
                    "sub_activity",
                    "La sous-activité ne correspond pas à l'activité sélectionnée.",
                )

        return cleaned

