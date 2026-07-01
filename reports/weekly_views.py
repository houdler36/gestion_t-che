from datetime import datetime, timedelta
from calendar import monthrange

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.models import User
from projects.models import Project
from tasks.models import Task
from tracking.models import DailyLog


def _parse_year_week(request):
    """Supporte week=<YYYY-WW> (input type="week") OU (year + week) en GET."""
    now = timezone.now().date()
    year_str = request.GET.get('year')
    week_str = request.GET.get('week')

    # Cas 1: week=YYYY-WW
    if week_str and isinstance(week_str, str) and '-' in week_str:
        try:
            y, w = week_str.split('-', 1)
            year = int(y)
            week = int(w)
            return year, week
        except ValueError:
            pass

    # Cas 2: year + week séparés
    year = int(year_str) if year_str else now.isocalendar()[0]
    week = int(week_str) if week_str else now.isocalendar()[1]
    return year, week


def _get_iso_week_bounds(year: int, week: int):
    # Lundi -> dimanche
    first_day = datetime.strptime(f'{year}-W{week:02d}-1', '%G-W%V-%u').date()
    last_day = first_day + timedelta(days=6)
    return first_day, last_day


class WeeklyReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/weekly_report_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        project_id = self.request.GET.get('project')
        user_id = self.request.GET.get('user')

        year, week = _parse_year_week(self.request)
        first_day, last_day = _get_iso_week_bounds(year, week)

        # Mois contexte pour limiter les semaines (si month fourni via GET)
        month_ctx = self.request.GET.get('month')
        if month_ctx and isinstance(month_ctx, str) and '-' in month_ctx:
            try:
                m_y, m_m = month_ctx.split('-', 1)
                month_ctx = f"{int(m_y):04d}-{int(m_m):02d}"
            except ValueError:
                month_ctx = None
        if not month_ctx:
            month_ctx = f"{first_day.year:04d}-{first_day.month:02d}"

        ctx_year = int(month_ctx.split('-', 1)[0])
        ctx_month = int(month_ctx.split('-', 1)[1])
        ctx_first_day = datetime(ctx_year, ctx_month, 1).date()
        ctx_last_day = datetime(ctx_year, ctx_month, monthrange(ctx_year, ctx_month)[1]).date()

        # Générer toutes les semaines ISO dont les bornes tombent dans le mois contexte
        start_probe = ctx_first_day - timedelta(days=7)
        end_probe = ctx_last_day + timedelta(days=7)

        allowed_weeks_set = set()
        d = start_probe
        while d <= end_probe:
            iso_y, iso_w, _ = d.isocalendar()
            allowed_weeks_set.add((iso_y, iso_w))
            d += timedelta(days=7)

        allowed_weeks = []
        for wy, ww in allowed_weeks_set:
            w_first, w_last = _get_iso_week_bounds(wy, ww)
            if w_last >= ctx_first_day and w_first <= ctx_last_day:
                allowed_weeks.append((wy, ww))

        allowed_weeks = sorted(allowed_weeks, key=lambda t: (t[0], t[1]))

        # Validation de week : si hors-liste => semaine la plus proche
        if (year, week) not in allowed_weeks:
            req_center = first_day + timedelta(days=3)

            def week_dist(pair):
                wf, _ = _get_iso_week_bounds(pair[0], pair[1])
                center = wf + timedelta(days=3)
                return abs((center - req_center).days)

            best = min(allowed_weeks, key=week_dist) if allowed_weeks else (year, week)
            year, week = best
            first_day, last_day = _get_iso_week_bounds(year, week)

        context.update({
            'month_ctx_ym': month_ctx,
            'allowed_weeks': allowed_weeks,
            'week': week,
            'year': year,
            'first_day': first_day,
            'last_day': last_day,
            'week_label': f'Semaine {week} - {first_day.strftime("%d/%m/%Y")} au {last_day.strftime("%d/%m/%Y")}',
        })

        role = getattr(user, 'role', None)

        if role == 'MEMBER':
            if not user_id or int(user_id) != user.id:
                user_id = str(user.id)
                selected_user = user
            else:
                selected_user = User.objects.filter(id=user_id).first()

            projects_qs = Project.objects.filter(members=user).order_by('name')
            users_qs = User.objects.filter(id=user.id, is_active=True).order_by('username')

        elif role == 'PM':
            projects_qs = Project.objects.filter(members=user).order_by('name')
            users_qs = User.objects.filter(projects__in=projects_qs).distinct().order_by('username')

            selected_user = None
            if user_id:
                try:
                    uid = int(user_id)
                    if not users_qs.filter(id=uid).exists():
                        user_id = None
                    else:
                        selected_user = users_qs.get(id=uid)
                except ValueError:
                    user_id = None

        else:
            projects_qs = Project.objects.all().order_by('name')
            users_qs = User.objects.filter(is_active=True).order_by('username')
            selected_user = None
            if user_id:
                try:
                    selected_user = users_qs.get(id=int(user_id))
                except (ValueError, User.DoesNotExist):
                    selected_user = None
                    user_id = None

        selected_project = None
        if project_id:
            try:
                selected_project = Project.objects.get(id=int(project_id))
            except (ValueError, Project.DoesNotExist):
                selected_project = None
                project_id = None

        context.update({
            'projects': projects_qs,
            'users': users_qs,
            'selected_project': selected_project,
            'selected_user': selected_user,
        })

        # =========================
        # PRESENCE (DailyLog) : 1 log = présent pour cette date
        # =========================
        time_entries = DailyLog.objects.filter(date__gte=first_day, date__lte=last_day)
        if project_id and selected_project:
            time_entries = time_entries.filter(task__project_id=project_id)
        if user_id and selected_user:
            time_entries = time_entries.filter(user_id=user_id)

        days_by_user = (
            time_entries.values('user__username', 'user__id')
            .annotate(days_present=Count('date', distinct=True), total_entries=Count('id'))
            .order_by('-days_present')
        )
        days_by_project = (
            time_entries.values('task__project__name', 'task__project__id')
            .annotate(days_present=Count('date', distinct=True), total_entries=Count('id'))
            .order_by('-days_present')
        )

        context['days_by_user'] = list(days_by_user)
        context['days_by_project'] = list(days_by_project)

        # =========================
        # TÂCHES (Task)
        # =========================
        tasks = Task.objects.filter(due_date__gte=first_day, due_date__lte=last_day)
        if project_id and selected_project:
            tasks = tasks.filter(Q(project_id=project_id) | Q(sub_activity__activity__project_id=project_id))
        if user_id and selected_user:
            tasks = tasks.filter(assigned_to_id=user_id)

        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='DONE').count()
        pending_tasks = tasks.filter(status__in=['TODO', 'INPROGRESS']).count()

        context.update({
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        })

        # Total jours de présence (somme par utilisateur)
        total_present_days_count = sum(r['days_present'] for r in days_by_user) if days_by_user else 0
        context['total_present_days'] = total_present_days_count

        # =========================
        # RAPPORT DÉTAILLÉ PAR PERSONNE
        # =========================
        report_by_person = []
        people = users_qs
        if user_id and selected_user:
            people = people.filter(id=selected_user.id)

        for u in people:
            u_time = time_entries.filter(user_id=u.id)
            u_tasks = tasks.filter(assigned_to_id=u.id)

            days_present = u_time.values('date').distinct().count()

            person_data = {
                'user': u,
                'total_present_days': days_present,
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

            u_project_days = (
                u_time.values('task__project__id', 'task__project__name')
                .annotate(days_present=Count('date', distinct=True), entries=Count('id'))
                .order_by('-days_present')
            )

            for pr in u_project_days:
                person_data['projects'].append({
                    'project__id': pr['task__project__id'],
                    'project__name': pr['task__project__name'],
                    'days': pr['days_present'],
                    'entries': pr['entries'],
                })

            if person_data['total_present_days'] > 0 or person_data['total_tasks'] > 0:
                report_by_person.append(person_data)

        context['report_by_person'] = report_by_person

        # =========================
        # DÉTAIL (1 ligne = 1 DailyLog)
        # =========================
        details_qs = time_entries.select_related(
            'user',
            'task',
            'task__project',
            'task__sub_activity',
            'task__sub_activity__activity',
        )

        weekly_details = []
        for log in details_qs.order_by('date'):
            task = log.task
            sub = getattr(task, 'sub_activity', None)
            act = getattr(sub, 'activity', None) if sub else None

            weekly_details.append({
                'user': log.user,
                'project__name': task.project.name if getattr(task, 'project', None) else (act.project.name if act and getattr(act, 'project', None) else ''),
                'date': log.date,
                'activity__name': act.name if act else '',
                'sub_activity__name': sub.name if sub else '',
                'task__name': task.name if task else '',
                'task__status_display': task.get_status_display() if task else '',
            })

        context['weekly_details'] = weekly_details
        return context


def export_weekly_report_csv(request):
    year, week = _parse_year_week(request)
    first_day, last_day = _get_iso_week_bounds(year, week)

    project_id = request.GET.get('project')
    user_id = request.GET.get('user')

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
    response['Content-Disposition'] = f'attachment; filename="rapport_{year}_W{week:02d}.csv"'

    import csv

    writer = csv.writer(response)
    writer.writerow(['Semaine', f'{year}-W{week:02d}'])
    writer.writerow(['Personne', 'Projet', 'Jours travaillés', 'Entrées logs', 'Tâches', 'Terminées', 'En cours', 'En retard'])

    days_by_user_project = (
        time_entries.values('user__username', 'user__id', 'task__project__name', 'task__project__id')
        .annotate(days_present=Count('date', distinct=True), entries=Count('id'))
    )

    for row in days_by_user_project:
        username = row['user__username']
        project_name = row['task__project__name'] or ''
        days = row['days_present'] or 0
        entries = row['entries']

        u_tasks = tasks.filter(assigned_to_id=row['user__id'])
        p_tasks = u_tasks.filter(
            Q(project_id=row['task__project__id']) | Q(sub_activity__activity__project_id=row['task__project__id'])
        )

        writer.writerow([
            f'{year}-W{week:02d}',
            username,
            project_name,
            days,
            entries,
            p_tasks.count(),
            p_tasks.filter(status='DONE').count(),
            p_tasks.filter(status__in=['TODO', 'INPROGRESS']).count(),
            p_tasks.filter(status__in=['TODO', 'INPROGRESS'], due_date__lt=timezone.now().date()).count(),
        ])

    return response
