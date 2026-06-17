from projects.models import Project
from tasks.models import Task


def sidebar_counts(request):
    """Compteurs globaux pour alimenter la sidebar."""
    context = {}

    if not request.user.is_authenticated:
        return context

    # Compteurs projets (admin)
    context['total_projects'] = Project.objects.count() if request.user.role == 'ADMIN' else 0

    # Compteurs tâches (membre)
    context['todo_count'] = Task.objects.filter(assigned_to=request.user, status='TODO').count()
    if request.user.role != 'MEMBER':
        context['todo_count'] = 0

    return context

