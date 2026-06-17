from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from projects.forms import ActivityForm, ProjectForm, SubActivityForm
from projects.models import Activity, Project, Project, SubActivity
from tasks.models import Task



# =====================
# Back-office auth
# =====================


class AdminOrPMMixin(UserPassesTestMixin):
    def test_func(self):
        return getattr(self.request.user, 'role', None) in ['ADMIN', 'PM']


# =====================
# VUES utilisateur
# =====================


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) == 'ADMIN':
            return Project.objects.all()
        return Project.objects.filter(members=user)


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()

        context['activities'] = project.activities.all()
        context['sub_activities'] = SubActivity.objects.filter(activity__project=project)

        context['tasks'] = Task.objects.filter(
            Q(sub_activity__activity__project=project) | Q(project=project)
        )

        if hasattr(project, 'get_progress'):
            context['progress'] = project.get_progress()
        else:
            context['progress'] = 0

        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    fields = ['name', 'description', 'start_date', 'end_date', 'status', 'members']
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Projet créé avec succès !')
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    fields = ['name', 'description', 'start_date', 'end_date', 'status', 'members']
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project_list')

    def form_valid(self, form):
        messages.success(self.request, 'Projet mis à jour avec succès !')
        return super().form_valid(form)


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('projects:project_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Projet supprimé avec succès !')
        return super().delete(request, *args, **kwargs)


# =====================
# VUES admin custom
# =====================


class AdminProjectListView(LoginRequiredMixin, AdminOrPMMixin, ListView):
    model = Project
    template_name = 'projects/admin/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) == 'ADMIN':
            return Project.objects.all().prefetch_related('members', 'activities')
        return Project.objects.filter(members=user).prefetch_related('members', 'activities')


class AdminProjectCreateView(LoginRequiredMixin, AdminOrPMMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/admin/project_form.html'

    def get_success_url(self):
        return reverse_lazy('projects:admin_project_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"✅ Projet '{form.instance.name}' créé avec succès !")
        return super().form_valid(form)


class AdminProjectDetailView(LoginRequiredMixin, AdminOrPMMixin, DetailView):
    model = Project
    template_name = 'projects/admin/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()

        context['activities'] = project.activities.all().prefetch_related(
            Prefetch('sub_activities', queryset=SubActivity.objects.all())
        )

        context['progress'] = project.get_progress() if hasattr(project, 'get_progress') else 0
        return context


class AdminProjectUpdateView(LoginRequiredMixin, AdminOrPMMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/admin/project_form.html'

    def get_success_url(self):
        return reverse_lazy('projects:admin_project_list')

    def form_valid(self, form):
        messages.success(self.request, f"✅ Projet '{form.instance.name}' mis à jour avec succès !")
        return super().form_valid(form)


class AdminProjectDeleteView(LoginRequiredMixin, AdminOrPMMixin, DeleteView):
    model = Project
    template_name = 'projects/admin/project_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, f"✅ Projet '{self.object.name}' supprimé avec succès !")
        return reverse_lazy('projects:admin_project_list')


class AdminActivityCreateView(LoginRequiredMixin, AdminOrPMMixin, CreateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'projects/admin/activity_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        kwargs['project'] = self.project
        return kwargs

    def form_valid(self, form):
        form.instance.project = self.project
        messages.success(self.request, f"✅ Activité '{form.instance.name}' créée avec succès !")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('projects:admin_project_detail', kwargs={'pk': self.project.pk})


class AdminActivityUpdateView(LoginRequiredMixin, AdminOrPMMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'projects/admin/activity_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        activity = self.get_object()
        kwargs['project'] = activity.project
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"✅ Activité '{form.instance.name}' mise à jour avec succès !")
        return super().form_valid(form)

    def get_success_url(self):
        activity = self.get_object()
        return reverse_lazy('projects:admin_project_detail', kwargs={'pk': activity.project.pk})


class AdminActivityDeleteView(LoginRequiredMixin, AdminOrPMMixin, DeleteView):
    model = Activity
    template_name = 'projects/admin/activity_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, f"✅ Activité '{self.object.name}' supprimée avec succès !")
        return reverse_lazy('projects:admin_project_detail', kwargs={'pk': self.object.project.pk})


class AdminSubActivityCreateView(LoginRequiredMixin, AdminOrPMMixin, CreateView):
    model = SubActivity
    form_class = SubActivityForm
    template_name = 'projects/admin/subactivity_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.activity = get_object_or_404(Activity, pk=self.kwargs['activity_pk'])
        kwargs['activity'] = self.activity
        return kwargs

    def form_valid(self, form):
        form.instance.activity = self.activity
        messages.success(self.request, f"✅ Sous-activité '{form.instance.name}' créée avec succès !")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('projects:admin_project_detail', kwargs={'pk': self.activity.project.pk})


class AdminSubActivityUpdateView(LoginRequiredMixin, AdminOrPMMixin, UpdateView):
    model = SubActivity
    form_class = SubActivityForm
    template_name = 'projects/admin/subactivity_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        sub = self.get_object()
        kwargs['activity'] = sub.activity
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"✅ Sous-activité '{form.instance.name}' mise à jour avec succès !")
        return super().form_valid(form)

    def get_success_url(self):
        sub = self.get_object()
        return reverse_lazy('projects:admin_project_detail', kwargs={'pk': sub.activity.project.pk})


class AdminSubActivityDeleteView(LoginRequiredMixin, AdminOrPMMixin, DeleteView):
    model = SubActivity
    template_name = 'projects/admin/subactivity_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, f"✅ Sous-activité '{self.object.name}' supprimée avec succès !")
        return reverse_lazy('projects:admin_project_detail', kwargs={'pk': self.object.activity.project.pk})

