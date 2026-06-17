from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from projects.models import Project
from tasks.models import Task
from tracking.models import DailyLog


@login_required
def dashboard(request):
    user = request.user

    if user.role == 'ADMIN':
        context = {
            'total_projects': Project.objects.count(),
            'total_tasks': Task.objects.count(),
            'tasks_done': Task.objects.filter(status='DONE').count(),
            'projects_ongoing': Project.objects.filter(status='ONGOING').count(),
            'tasks_overdue': Task.objects.filter(
                due_date__lt=timezone.now().date(),
                status__in=['TODO', 'INPROGRESS'],
            ).count(),
        }

        return render(request, 'dashboard.html', context)

    if user.role == 'PM':
        my_projects = Project.objects.filter(members=user)
        my_tasks = Task.objects.filter(sub_activity__activity__project__in=my_projects)

        context = {
            'my_projects': my_projects,
            'my_projects_count': my_projects.count(),
            'my_tasks': my_tasks,
            'my_tasks_count': my_tasks.count(),
            'my_tasks_done': my_tasks.filter(status='DONE').count(),
        }

        return render(request, 'dashboard.html', context)

    # Member
    my_tasks = Task.objects.filter(assigned_to=user)
    context = {
        'my_tasks': my_tasks,
        'todo_count': my_tasks.filter(status='TODO').count(),
        'inprogress_count': my_tasks.filter(status='INPROGRESS').count(),
        'done_count': my_tasks.filter(status='DONE').count(),
        'overdue_count': my_tasks.filter(
            due_date__lt=timezone.now().date(),
            status__in=['TODO', 'INPROGRESS'],
        ).count(),
        'recent_logs': DailyLog.objects.filter(user=user).order_by('-date')[:5],
    }
    return render(request, 'dashboard.html', context)

