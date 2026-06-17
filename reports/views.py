from django.views.generic import TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Count, Q
from django.utils import timezone
import csv

from projects.models import Project
from tasks.models import Task
from accounts.models import User
from tracking.models import DailyLog


class ReportDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/report_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.role == 'ADMIN':
            context['total_projects'] = Project.objects.count()
            context['total_tasks'] = Task.objects.count()
            context['tasks_done'] = Task.objects.filter(status='DONE').count()
            context['tasks_todo'] = Task.objects.filter(status='TODO').count()
            context['tasks_overdue'] = Task.objects.filter(
                due_date__lt=timezone.now().date(),
                status__in=['TODO', 'INPROGRESS'],
            ).count()

            context['top_projects'] = Project.objects.annotate(
                task_count=Count('activities__sub_activities__tasks')
            ).order_by('-task_count')[:5]

            context['top_users'] = User.objects.annotate(
                task_count=Count('assigned_tasks')
            ).order_by('-task_count')[:5]
        else:
            if user.role == 'PM':
                projects = Project.objects.filter(members=user)
            else:
                projects = Project.objects.none()

            context['projects'] = projects
            context['my_tasks_count'] = Task.objects.filter(assigned_to=user).count()
            context['my_tasks_done'] = Task.objects.filter(assigned_to=user, status='DONE').count()
            context['my_tasks_overdue'] = Task.objects.filter(
                assigned_to=user,
                due_date__lt=timezone.now().date(),
                status__in=['TODO', 'INPROGRESS'],
            ).count()

        return context


class ProjectReportView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'reports/project_report.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()

        tasks = Task.objects.filter(Q(sub_activity__activity__project=project) | Q(project=project))

        context['total_tasks'] = tasks.count()
        context['tasks_done'] = tasks.filter(status='DONE').count()
        context['tasks_todo'] = tasks.filter(status='TODO').count()
        context['tasks_inprogress'] = tasks.filter(status='INPROGRESS').count()
        context['tasks_blocked'] = tasks.filter(status='BLOCKED').count()
        context['tasks_overdue'] = tasks.filter(
            due_date__lt=timezone.now().date(),
            status__in=['TODO', 'INPROGRESS'],
        ).count()

        context['tasks_by_member'] = {}
        for member in project.members.all():
            member_tasks = tasks.filter(assigned_to=member)
            context['tasks_by_member'][member] = {
                'total': member_tasks.count(),
                'done': member_tasks.filter(status='DONE').count(),
                'overdue': member_tasks.filter(
                    due_date__lt=timezone.now().date(),
                    status__in=['TODO', 'INPROGRESS'],
                ).count(),
            }

        if hasattr(project, 'get_progress'):
            context['progress'] = project.get_progress()
        else:
            context['progress'] = 0

        return context


class UserReportView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'reports/user_report.html'
    context_object_name = 'user_report'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_report = self.get_object()

        tasks = Task.objects.filter(assigned_to=user_report)

        context['total_tasks'] = tasks.count()
        context['tasks_done'] = tasks.filter(status='DONE').count()
        context['tasks_todo'] = tasks.filter(status='TODO').count()
        context['tasks_inprogress'] = tasks.filter(status='INPROGRESS').count()
        context['tasks_blocked'] = tasks.filter(status='BLOCKED').count()
        context['tasks_overdue'] = tasks.filter(
            due_date__lt=timezone.now().date(),
            status__in=['TODO', 'INPROGRESS'],
        ).count()

        context['tasks_by_project'] = {}
        for task in tasks.select_related('sub_activity__activity', 'project', 'assigned_to'):
            if task.sub_activity:
                project = task.sub_activity.activity.project
            elif task.project:
                project = task.project
            else:
                continue
            context['tasks_by_project'][project] = context['tasks_by_project'].get(project, 0) + 1

        context['logs_count'] = DailyLog.objects.filter(user=user_report).count()
        return context


def export_project_report(request, pk):
    project = get_object_or_404(Project, pk=pk)
    tasks = Task.objects.filter(Q(sub_activity__activity__project=project) | Q(project=project))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="rapport_{project.name}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Tâche', 'Assigné à', 'Priorité', 'Statut', 'Date limite', 'Retard'])

    for task in tasks.select_related('assigned_to'):
        writer.writerow([
            task.name,
            task.assigned_to.username,
            task.get_priority_display(),
            task.get_status_display(),
            task.due_date,
            'Oui' if getattr(task, 'is_overdue', lambda: task.due_date < timezone.now().date()) else 'Non',
        ])

    return response

