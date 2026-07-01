from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.db.models import Q
from django.shortcuts import redirect


from tasks.models import Task
from gestprojet.tasks.forms import TaskForm




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
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super().get_initial()

        # ✅ Valeurs temporaires stockées en session (persistent même après refresh)
        project_id = self.request.session.get('temp_project_id')
        activity_id = self.request.session.get('temp_activity_id')

        if project_id:
            initial['project'] = project_id

        if activity_id:
            initial['activity'] = activity_id

        # ⚠️ Empêche les incohérences : si on recharge les activités, la sous-activité
        # peut être incompatible avec la nouvelle activité => on la neutralise.
        action = self.request.GET.get('action')
        if action == 'refresh_activities':
            initial['sub_activity'] = None

        return initial


    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'refresh_activities':
            project_id = request.POST.get('project_id') or request.POST.get('project')
            if project_id:
                request.session['temp_project_id'] = project_id
                request.session['temp_activity_id'] = None
            return redirect(request.path)

        if action == 'refresh_sub_activities':
            activity_id = request.POST.get('activity_id') or request.POST.get('activity')
            if activity_id:
                request.session['temp_activity_id'] = activity_id
            return redirect(request.path)

        return super().post(request, *args, **kwargs)


    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Tâche créée avec succès !')
        return super().form_valid(form)






class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')

    def get_initial(self):
        initial = super().get_initial()

        project_id = self.request.session.get('temp_project_id')
        activity_id = self.request.session.get('temp_activity_id')

        if project_id:
            initial['project'] = project_id
        if activity_id:
            initial['activity'] = activity_id

        # ⚠️ Empêche les incohérences : si on recharge les activités, la sous-activité
        # peut être incompatible avec la nouvelle activité => on la neutralise.
        action = self.request.GET.get('action')
        if action == 'refresh_activities':
            initial['sub_activity'] = None

        return initial


    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'refresh_activities':
            project_id = request.POST.get('project_id') or request.POST.get('project')
            if project_id:
                request.session['temp_project_id'] = project_id
                request.session['temp_activity_id'] = None
            return redirect(request.path)

        if action == 'refresh_sub_activities':
            activity_id = request.POST.get('activity_id') or request.POST.get('activity')
            if activity_id:
                request.session['temp_activity_id'] = activity_id
            return redirect(request.path)

        if action == 'save':
            request.session.pop('temp_project_id', None)
            request.session.pop('temp_activity_id', None)
            return super().post(request, *args, **kwargs)

        return super().post(request, *args, **kwargs)


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

