from datetime import datetime
from calendar import monthrange

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.models import User
from projects.models import Project
from tasks.models import Task
from tracking.models import DailyLog


def _get_month_bounds(year: int, month: int):
    first_day = datetime(year, month, 1).date()
    last_day = datetime(year, month, monthrange(year, month)[1]).date()
    return first_day, last_day


class MonthlyReportDashboardView(LoginRequiredMixin, TemplateView):

    template_name = 'reports/monthly_report_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        # Supporte month=<YYYY-MM> (input type="month") OU month=<int>.
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')

        if month and isinstance(month, str) and '-' in month:
            # YYYY-MM
            try:
                year_str, month_str = month.split('-', 1)
                year = int(year_str)
                month = int(month_str)
            except ValueError:
                year = now.year
                month = now.month
        else:
            year = int(year) if year else int(now.year)
            month = int(month) if month else int(now.month)

        project_id = self.request.GET.get('project')
        user_id = self.request.GET.get('user')

        first_day, last_day = _get_month_bounds(year, month)

        context.update({
            'year': year,
            'month': month,
            'first_day': first_day,
            'last_day': last_day,
            'month_name': first_day.strftime('%B %Y'),
        })

        user = self.request.user

        # Règles de permissions :
        # - Admin : tous les rapports (toutes les personnes, tous les projets)
        # - Membre : uniquement son propre rapport (lui-même)
        # - Chef de projet (role='PM') : rapport de ses projets (tous les membres du projet)
        role = getattr(user, 'role', None)

        if role == 'MEMBER':
            # Force user filter à soi-même
            if not user_id or int(user_id) != user.id:
                user_id = str(user.id)
                selected_user = user
                user_filter = Q(user_id=user.id)

            projects_qs = Project.objects.filter(members=user).order_by('name')
            users_qs = User.objects.filter(id=user.id, is_active=True).order_by('username')

        elif role == 'PM':
            projects_qs = Project.objects.filter(members=user).order_by('name')
            users_qs = User.objects.filter(projects__in=projects_qs).distinct().order_by('username')

            # Si un utilisateur est demandé, s'assurer qu'il est dans les membres autorisés
            if user_id:
                try:
                    if not users_qs.filter(id=int(user_id)).exists():
                        user_id = None
                        selected_user = None
                        user_filter = Q()
                except ValueError:
                    user_id = None

        else:
            projects_qs = Project.objects.all().order_by('name')
            users_qs = User.objects.filter(is_active=True).order_by('username')



        selected_project = None
        project_filter = Q()
        if project_id:
            selected_project = Project.objects.get(id=project_id)
            project_filter = Q(project_id=project_id)

        selected_user = None
        user_filter = Q()
        if user_id:
            selected_user = User.objects.get(id=user_id)
            user_filter = Q(user_id=user_id)

        context['projects'] = projects_qs
        context['users'] = users_qs
        context['selected_project'] = selected_project
        context['selected_user'] = selected_user

        # =========================
        # HEURES (DailyLog)
        # =========================
        # DailyLog -> task -> project
        time_entries = DailyLog.objects.filter(date__gte=first_day, date__lte=last_day)
        if project_id:
            time_entries = time_entries.filter(task__project_id=project_id)
        if user_id:
            time_entries = time_entries.filter(user_id=user_id)

        # total_hours: time_spent_minutes is integer minutes
        hours_by_user = (
            time_entries.values('user__username', 'user__id')
            .annotate(total_minutes=Sum('time_spent_minutes'), total_entries=Count('id'))
            .order_by('-total_minutes')
        )
        for row in hours_by_user:
            total_minutes = row['total_minutes'] or 0
            row['total_hours'] = round(total_minutes / 60, 2)

        hours_by_project = (
            time_entries.values('task__project__name', 'task__project__id')
            .annotate(total_minutes=Sum('time_spent_minutes'), total_entries=Count('id'))
            .order_by('-total_minutes')
        )
        for row in hours_by_project:
            total_minutes = row['total_minutes'] or 0
            row['total_hours'] = round(total_minutes / 60, 2)

        context['hours_by_user'] = list(hours_by_user)
        context['hours_by_project'] = list(hours_by_project)

        # =========================
        # TÂCHES (Task)
        # =========================
        # Filtre temporel: due_date dans le mois
        tasks = Task.objects.filter(due_date__gte=first_day, due_date__lte=last_day)
        if project_id:
            tasks = tasks.filter(Q(project_id=project_id) | Q(sub_activity__activity__project_id=project_id))
        if user_id:
            tasks = tasks.filter(assigned_to_id=user_id)

        tasks_by_user = (
            tasks.values('assigned_to__username', 'assigned_to__id')
            .annotate(
                total=Count('id'),
                completed=Count('id', filter=Q(status='DONE')),
                pending=Count('id', filter=Q(status__in=['TODO', 'INPROGRESS'])),
                overdue=Count(
                    'id',
                    filter=Q(
                        status__in=['TODO', 'INPROGRESS'],
                        due_date__lt=timezone.now().date(),
                    ),
                ),
            )
            .order_by('-total')
        )
        context['tasks_by_user'] = list(tasks_by_user)

        # =========================
        # STATISTIQUES GLOBALES
        # =========================
        total_minutes = time_entries.aggregate(total=Sum('time_spent_minutes'))['total'] or 0
        total_hours = round(total_minutes / 60, 2)

        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='DONE').count()
        pending_tasks = tasks.filter(status__in=['TODO', 'INPROGRESS']).count()

        context.update({
            'total_hours': total_hours,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        })

        # =========================
        # RAPPORT DÉTAILLÉ PAR PERSONNE
        # =========================
        report_by_person = []

        # Utiliser les utilisateurs filtrés si project_id / user_id sont fournis
        people = users_qs
        if user_id:
            people = people.filter(id=user_id)
        # Si le rôle ADMIN est requis ici, on le fait côté template/permissions globales

        for u in people:
            u_time = time_entries.filter(user_id=u.id)
            u_tasks = tasks.filter(assigned_to_id=u.id)

            u_total_minutes = u_time.aggregate(total=Sum('time_spent_minutes'))['total'] or 0

            person_data = {
                'user': u,
                'total_hours': round(u_total_minutes / 60, 2),
                'total_entries': u_time.count(),
                'total_tasks': u_tasks.count(),
                'completed_tasks': u_tasks.filter(status='DONE').count(),
                'pending_tasks': u_tasks.filter(status__in=['TODO', 'INPROGRESS']).count(),
                'overdue_tasks': u_tasks.filter(
                    status__in=['TODO', 'INPROGRESS'],
                    due_date__lt=timezone.now().date(),
                ).count(),
                'projects': [],
            }

            # Projets de temps pour cette personne sur la période
            # (évite N+1 en agrégeant une seule fois)
            u_project_hours = (
                u_time.values('task__project__id', 'task__project__name')
                .annotate(total_minutes=Sum('time_spent_minutes'), entries=Count('id'))
                .order_by('-total_minutes')
            )

            for pr in u_project_hours:
                hours = round((pr['total_minutes'] or 0) / 60, 2)
                if hours <= 0:
                    continue
                person_data['projects'].append({
                    'project__id': pr['task__project__id'],
                    'project__name': pr['task__project__name'],
                    'hours': hours,
                    'entries': pr['entries'],
                })

            # Garder seulement les personnes qui ont des données
            if person_data['total_hours'] > 0 or person_data['total_tasks'] > 0:
                report_by_person.append(person_data)

        context['report_by_person'] = report_by_person

        # =========================
        # DÉTAIL (1 ligne = 1 DailyLog)
        # =========================
        # DailyLog -> task (statut) -> sub_activity/activity
        details_qs = (
            time_entries.select_related(
                'user',
                'task',
                'task__project',
                'task__sub_activity',
                'task__sub_activity__activity',
            )
        )


        # Filtrage : certaines routes peuvent laisser passer un task sans sub_activity
        # => on affiche activité/sous-activité à vide.
        monthly_details = []
        for log in details_qs.order_by('date'):
            task = log.task
            sub = getattr(task, 'sub_activity', None)
            act = getattr(sub, 'activity', None) if sub else None

            # Heures depuis le log
            minutes = log.time_spent_minutes or 0
            hours = round(minutes / 60, 2)

            monthly_details.append({
                'user': log.user,
                'project__name': task.project.name if getattr(task, 'project', None) else (act.project.name if act and getattr(act, 'project', None) else ''),
                'date': log.date,
                'activity__name': act.name if act else '',
                'sub_activity__name': sub.name if sub else '',
                'task__name': task.name if task else '',
                'task__status': task.status if task else '',
                'task__status_display': task.get_status_display() if task else '',
                'hours': hours,
            })

        context['monthly_details'] = monthly_details


        # Pour Chart.js: préparer des structures simples
        context['hours_by_project_chart'] = [
            {'label': d['task__project__name'], 'hours': d['total_hours']}
            for d in hours_by_project
        ]
        context['tasks_by_user_chart'] = [
            {
                'label': d['assigned_to__username'],
                'completed': d['completed'],
                'pending': d['pending'],
                'overdue': d['overdue'],
            }
            for d in tasks_by_user
        ]

        return context


def export_monthly_report_csv(request):
    now = timezone.now()
    year = request.GET.get('year')
    month = request.GET.get('month')

    if month and isinstance(month, str) and '-' in month:
        try:
            year_str, month_str = month.split('-', 1)
            year = int(year_str)
            month = int(month_str)
        except ValueError:
            year = now.year
            month = now.month
    else:
        year = int(year) if year else int(now.year)
        month = int(month) if month else int(now.month)

    project_id = request.GET.get('project')
    user_id = request.GET.get('user')

    first_day, last_day = _get_month_bounds(year, month)

    time_entries = DailyLog.objects.filter(date__gte=first_day, date__lte=last_day)
    if project_id:
        time_entries = time_entries.filter(task__project_id=project_id)
    if user_id:
        time_entries = time_entries.filter(user_id=user_id)

    tasks = Task.objects.filter(due_date__gte=first_day, due_date__lte=last_day)
    if project_id:
        tasks = tasks.filter(Q(project_id=project_id) | Q(sub_activity__activity__project_id=project_id))
    if user_id:
        tasks = tasks.filter(assigned_to_id=user_id)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="rapport_{year}_{month:02d}.csv"'

    import csv

    writer = csv.writer(response)
    writer.writerow(['Mois', f'{year}-{month:02d}'])
    writer.writerow(['Personne', 'Projet', 'Heures (h)', 'Entrées heures', 'Tâches', 'Terminées', 'En cours', 'En retard'])

    # Agrégation: minutes par (user, project)
    minutes_by_user_project = (
        time_entries.values('user__username', 'user__id', 'task__project__name', 'task__project__id')
        .annotate(total_minutes=Sum('time_spent_minutes'), entries=Count('id'))
    )

    for row in minutes_by_user_project:
        username = row['user__username']
        project_name = row['task__project__name'] or ''
        hours = round((row['total_minutes'] or 0) / 60, 2)
        entries = row['entries']

        u_tasks = tasks.filter(assigned_to_id=row['user__id'])
        p_tasks = u_tasks.filter(Q(project_id=row['task__project__id']) | Q(sub_activity__activity__project_id=row['task__project__id']))

        writer.writerow([
            f'{year}-{month:02d}',
            username,
            project_name,
            hours,
            entries,
            p_tasks.count(),
            p_tasks.filter(status='DONE').count(),
            p_tasks.filter(status__in=['TODO', 'INPROGRESS']).count(),
            p_tasks.filter(status__in=['TODO', 'INPROGRESS'], due_date__lt=timezone.now().date()).count(),
        ])

    return response

