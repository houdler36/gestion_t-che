from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import models

from projects.models import Project
from tasks.models import Task
from tracking.models import DailyLog



@login_required
def dashboard(request):
    """Dashboard modernisé (template unifié)."""
    user = request.user
    now = timezone.now()
    today = now.date()

    # 1) Périmètre des tâches selon le rôle (données), sans changer la structure UI.
    if user.role == 'ADMIN':
        tasks_qs = Task.objects.all()
    elif user.role == 'PM':
        my_projects = Project.objects.filter(members=user)
        tasks_qs = Task.objects.filter(sub_activity__activity__project__in=my_projects)
    else:
        tasks_qs = Task.objects.filter(assigned_to=user)

    # 2) Statistiques cartes
    tasks_total = tasks_qs.count()
    tasks_done = tasks_qs.filter(status='DONE').count()

    # Temps total (présence) : 1 DailyLog distinct = 1 jour de présence
    logs_qs = DailyLog.objects.filter(user=user).order_by('-date')
    recent_logs = list(logs_qs[:5])

    distinct_present_days = logs_qs.values('date').distinct().count()
    time_spent_hours = distinct_present_days

    recent_logs_count = len(recent_logs)

    # 3) Évolution (simple heuristique: variation vs hier si possible sinon 0)
    yesterday = today - timezone.timedelta(days=1)

    def delta_color_and_text(current, prev):
        if prev in (None, 0):
            return ('#64748b', '0%')
        pct = ((current - prev) / prev) * 100
        arrow = '↑' if pct >= 0 else '↓'
        abs_pct = abs(round(pct))
        if pct >= 0:
            return ('var(--success)', f'{arrow}{abs_pct} %')
        return ('var(--danger)', f'{arrow}{abs_pct} %')

    # Variation des tâches totales (créées) et terminées (terminées)
    created_today = tasks_qs.filter(created_at__date=today).count()
    created_yesterday = tasks_qs.filter(created_at__date=yesterday).count()
    tasks_delta_color, tasks_delta_text = delta_color_and_text(created_today or tasks_total, created_yesterday or tasks_total)

    done_today = tasks_qs.filter(status='DONE', updated_at__date=today).count()
    done_yesterday = tasks_qs.filter(status='DONE', updated_at__date=yesterday).count()
    done_delta_color, done_delta_text = delta_color_and_text(done_today or tasks_done, done_yesterday or tasks_done)

    logs_today = logs_qs.filter(date=today).count()
    logs_yesterday = logs_qs.filter(date=yesterday).count()
    logs_delta_color, logs_delta_text = delta_color_and_text(logs_today, logs_yesterday)

    # Variation temps (désormais = variation du nombre de jours de présence)
    days_today = logs_qs.filter(date=today).values('date').distinct().count()
    days_yesterday = logs_qs.filter(date=yesterday).values('date').distinct().count()
    try:
        time_delta_color, time_delta_text = delta_color_and_text(days_today or time_spent_hours, days_yesterday or time_spent_hours)
    except Exception:
        time_delta_color, time_delta_text = ('#64748b', '0%')

    # 4) Progression globale (basée sur DONE vs total)
    progression_percent = 0
    if tasks_total:
        progression_percent = int((tasks_done / tasks_total) * 100)

    def progression_bucket(p):
        if p < 35:
            return ('var(--danger)', 'Faible')
        if p < 70:
            return ('var(--warning)', 'Moyen')
        return ('var(--success)', 'Élevé')

    progression_color, progression_label = progression_bucket(progression_percent)

    # 5) Tâches en cours (top 6)
    tasks_in_progress_qs = tasks_qs.filter(status__in=['TODO', 'INPROGRESS', 'DONE', 'BLOCKED']).order_by('-updated_at')[:6]

    def task_progress(task):
        # On n’a pas de champ progress direct sur Task. On dérive depuis status.
        if task.status == 'DONE':
            return 100, 'var(--success)'
        if task.status == 'INPROGRESS':
            return 75, 'var(--primary)'
        if task.status == 'BLOCKED':
            return 20, 'var(--border)'
        return 20, 'var(--warning)'

    tasks_in_progress = []
    for t in tasks_in_progress_qs:
        p, c = task_progress(t)
        tasks_in_progress.append({
            'name': t.name,
            'priority': t.priority,
            'status': t.status,
            'progress': p,
            'progress_color': c,
        })

    # 6) Activités récentes : on reconstruit un mini libellé depuis les DailyLog.
    # On n’a pas d’audit log global, donc on mappe le type à partir du delta progress_delta.
    def when_label(d):
        delta = now - timezone.make_aware(timezone.datetime.combine(d, timezone.datetime.min.time()))
        hours = int(delta.total_seconds() // 3600)
        if hours <= 0:
            return 'À l’instant'
        if hours < 24:
            return f'il y a {hours} heure(s)'
        days = hours // 24
        if days == 1:
            return 'Hier'
        return f'il y a {days} jour(s)'

    recent_logs_payload = []
    for l in recent_logs:
        kind = 'update'
        title = f"Modification d'un Daily Log"
        if l.progress_delta and l.progress_delta > 0:
            kind = 'update'
            title = f"Log mis à jour : +{l.progress_delta} progression"
        elif l.progress_delta and l.progress_delta == 0:
            kind = 'update'
            title = f"Modification d'un Daily Log"

        recent_logs_payload.append({
            'kind': kind,
            'title': title,
            'when': when_label(l.date),
        })

    context = {
        'user': user,
        'today': today.strftime('%d %B %Y').replace('.', ''),
        'tasks_total': tasks_total,
        'tasks_done': tasks_done,
        'recent_logs_count': recent_logs_count,
        'time_spent_hours': time_spent_hours,
        'recent_logs': recent_logs_payload,
        'tasks_in_progress': tasks_in_progress,
        'progression_percent': progression_percent,
        'progression_color': progression_color,
        'progression_label': progression_label,
        'tasks_delta_color': tasks_delta_color,
        'tasks_delta_text': tasks_delta_text,
        'done_delta_color': done_delta_color,
        'done_delta_text': done_delta_text,
        'logs_delta_color': logs_delta_color,
        'logs_delta_text': logs_delta_text,
        'time_delta_color': time_delta_color,
        'time_delta_text': time_delta_text,
    }

    return render(request, 'dashboard.html', context)


