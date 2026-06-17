from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.db.models import Q

from projects.models import SubActivity
from tasks.models import Task



class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) in ['ADMIN', 'PM']:
            return Task.objects.all()
        return Task.objects.filter(assigned_to=user)


class MyTaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/my_tasks.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        user = self.request.user
        # Pour un MEMBER :
        # - tâches assignées directement (assigned_to=user)
        # - OU tâches liées à un projet où l'utilisateur est membre.
        #
        # IMPORTANT : on évite de dépendre de user.projects.all() car si les
        # ProjectMembership ne sont pas peuplés correctement, ça peut renvoyer
        # 0 projet.
        project_ids = (
            user.projects.through.objects.filter(user_id=user.id).values_list('project_id', flat=True)
        )

        return (
            Task.objects.filter(
                (
                    Q(assigned_to=user)
                    | Q(project__id__in=project_ids)
                    | Q(sub_activity__activity__project__id__in=project_ids)
                )
            )
            .distinct()
        )






class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    fields = ['sub_activity', 'project', 'name', 'description', 'assigned_to', 'priority', 'due_date', 'status']
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Tâche créée avec succès !')
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if getattr(self.request.user, 'role', None) == 'PM':
            user_projects = self.request.user.projects.all()
            form.fields['sub_activity'].queryset = SubActivity.objects.filter(
                activity__project__in=user_projects
            )
            # Sécurise l'option "vide" pour permettre les tâches hors projet.
            # (Le champ est null=True/blank=True côté modèle, mais on force ici
            # la présence d'une option vide.)
            try:
                form.fields['sub_activity'].empty_label = "---------"
            except Exception:
                pass

        # Sécurise aussi l'option vide pour "project".
        try:
            form.fields['project'].empty_label = "---------"
        except Exception:
            pass

        return form



class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    fields = ['name', 'description', 'assigned_to', 'priority', 'due_date', 'status']
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tâche mise à jour avec succès !')
        return super().form_valid(form)


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tâche supprimée avec succès !')
        return super().delete(request, *args, **kwargs)

