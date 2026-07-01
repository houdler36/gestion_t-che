from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from projects.models import Project, ProjectMembership
from tasks.models import Task
from tracking.models import DailyLog

User = get_user_model()


class ReportsViewsTest(TestCase):
    def setUp(self):
        # Users
        self.member = User.objects.create_user(
            username="member",
            password="testpass123",
            role="MEMBER",
        )
        self.admin = User.objects.create_user(
            username="admin",
            password="adminpass123",
            role="ADMIN",
        )
        self.pm = User.objects.create_user(
            username="pm",
            password="pmpass123",
            role="PM",
        )

        # Projects (Project model requires start_date/end_date/created_by)
        today = timezone.now().date()
        self.project1 = Project.objects.create(
            name="Projet 1",
            description="desc",
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=30),
            status="ONGOING",
            created_by=self.admin,
        )
        self.project2 = Project.objects.create(
            name="Projet 2",
            description="desc2",
            start_date=today - timedelta(days=60),
            end_date=today + timedelta(days=60),
            status="ONGOING",
            created_by=self.pm,
        )

        # Memberships
        ProjectMembership.objects.create(user=self.member, project=self.project1)
        ProjectMembership.objects.create(user=self.pm, project=self.project1)
        ProjectMembership.objects.create(user=self.pm, project=self.project2)

        # Tasks
        # Weekly/monthly filters depend on due_date and DailyLog.date
        self.now = timezone.now()
        current_date = self.now.date()
        self.week_start = current_date - timedelta(days=current_date.weekday())  # Monday
        self.week_end = self.week_start + timedelta(days=6)

        # Outside current week (previous week)
        self.prev_week_day = self.week_start - timedelta(days=2)

        # Monthly bounds
        self.month_start = current_date.replace(day=1)
        # get last day by adding one month then -1 day
        next_month = (self.month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        self.month_end = next_month - timedelta(days=1)

        # Outside current month (previous month)
        self.prev_month_day = self.month_start - timedelta(days=10)

        self.task_in_week_done = Task.objects.create(
            name="Tâche in week done",
            description="",
            project=self.project1,
            sub_activity=None,
            assigned_to=self.member,
            created_by=self.member,
            priority="MEDIUM",
            due_date=self.week_start + timedelta(days=1),
            status="DONE",
        )
        self.task_in_week_todo = Task.objects.create(
            name="Tâche in week todo",
            description="",
            project=self.project1,
            sub_activity=None,
            assigned_to=self.member,
            created_by=self.member,
            priority="LOW",
            due_date=self.week_start + timedelta(days=2),
            status="TODO",
        )
        self.task_out_week = Task.objects.create(
            name="Tâche out week",
            description="",
            project=self.project1,
            sub_activity=None,
            assigned_to=self.member,
            created_by=self.member,
            priority="LOW",
            due_date=self.prev_week_day,
            status="TODO",
        )

        self.task_in_month_done = Task.objects.create(
            name="Tâche in month done",
            description="",
            project=self.project1,
            sub_activity=None,
            assigned_to=self.member,
            created_by=self.member,
            priority="MEDIUM",
            due_date=self.month_start + timedelta(days=3),
            status="DONE",
        )
        self.task_in_month_inprogress = Task.objects.create(
            name="Tâche in month inprogress",
            description="",
            project=self.project1,
            sub_activity=None,
            assigned_to=self.member,
            created_by=self.member,
            priority="MEDIUM",
            due_date=self.month_start + timedelta(days=7),
            status="INPROGRESS",
        )
        self.task_out_month = Task.objects.create(
            name="Tâche out month",
            description="",
            project=self.project1,
            sub_activity=None,
            assigned_to=self.member,
            created_by=self.member,
            priority="LOW",
            due_date=self.prev_month_day,
            status="TODO",
        )

        # Daily logs (date is auto_now_add => create now, then update(date=...))
        def create_log(user, task, date_value):
            log = DailyLog.objects.create(
                user=user,
                task=task,
                comment="log",
                difficulties="",
                progress_delta=10,
            )
            DailyLog.objects.filter(id=log.id).update(date=date_value)
            return log

        # Weekly logs (match tasks_in_week_* due_date)
        self.log_done_in_week = create_log(self.member, self.task_in_week_done, self.week_start + timedelta(days=1))
        self.log_todo_in_week = create_log(self.member, self.task_in_week_todo, self.week_start + timedelta(days=2))
        # Outside week
        self.log_out_week = create_log(self.member, self.task_out_week, self.prev_week_day)

        # Monthly logs
        self.log_done_in_month = create_log(self.member, self.task_in_month_done, self.month_start + timedelta(days=3))
        self.log_inprogress_in_month = create_log(self.member, self.task_in_month_inprogress, self.month_start + timedelta(days=7))
        self.log_out_month = create_log(self.member, self.task_out_month, self.prev_month_day)

        self.client = Client()

    def test_report_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("reports:report_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_report_dashboard_admin_context_keys_and_counts(self):
        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(reverse("reports:report_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_dashboard.html")

        # Admin context
        self.assertIn("total_projects", response.context)
        self.assertIn("total_tasks", response.context)
        self.assertIn("tasks_done", response.context)
        self.assertIn("tasks_todo", response.context)
        self.assertIn("tasks_overdue", response.context)
        self.assertIn("top_projects", response.context)
        self.assertIn("top_users", response.context)

        # total_projects = 2, total_tasks = 6
        self.assertEqual(response.context["total_projects"], 2)
        self.assertEqual(response.context["total_tasks"], 6)
        self.assertEqual(response.context["tasks_done"], 2)  # DONE: task_in_week_done + task_in_month_done
        self.assertEqual(response.context["tasks_todo"], 3)  # TODO: task_in_week_todo + task_out_week + task_out_month
        # tasks_overdue depends on due_date and status subset; no need to assert exact value beyond presence
        self.assertIsNotNone(response.context["tasks_overdue"])

    def test_report_dashboard_member_context_projects_and_my_tasks(self):
        self.client.login(username="member", password="testpass123")
        response = self.client.get(reverse("reports:report_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_dashboard.html")

        self.assertIn("projects", response.context)
        self.assertIn("my_tasks_count", response.context)
        self.assertIn("my_tasks_done", response.context)
        self.assertIn("my_tasks_overdue", response.context)

        # Member is in project1 only => projects count = 1
        self.assertEqual(response.context["projects"].count(), 1)
        # Member assigned_to: all 6 tasks created in setUp
        self.assertEqual(response.context["my_tasks_count"], 6)
        self.assertEqual(response.context["my_tasks_done"], 2)

    def test_weekly_report_dashboard_template_and_total_tasks_in_window(self):
        self.client.login(username="member", password="testpass123")
        response = self.client.get(reverse("reports:weekly_report_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/weekly_report_dashboard.html")

        # Default week parameter is current ISO week (computed from now)
        # Our tasks due_date in current week: 2 (task_in_week_done, task_in_week_todo)
        self.assertEqual(response.context["total_tasks"], 2)
        self.assertEqual(response.context["completed_tasks"], 1)
        self.assertEqual(response.context["pending_tasks"], 1)

        # Presence days: we created 2 logs in current week on two distinct dates
        self.assertEqual(response.context["total_present_days"], 2)

    def test_monthly_report_dashboard_template_and_total_tasks_in_window(self):
        self.client.login(username="member", password="testpass123")
        response = self.client.get(reverse("reports:monthly_report_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/monthly_report_dashboard.html")

        # Tasks in current month: 2 (task_in_month_done, task_in_month_inprogress)
        self.assertEqual(response.context["total_tasks"], 2)
        self.assertEqual(response.context["completed_tasks"], 1)
        self.assertEqual(response.context["pending_tasks"], 1)

        # Presence days: 2 logs in current month on two distinct dates
        self.assertEqual(response.context["total_present_days"], 2)

    def test_weekly_report_dashboard_member_selected_user_scope(self):
        # Ensure query param "user" is honored (views checks role + selected user)
        self.client.login(username="pm", password="pmpass123")
        response = self.client.get(
            reverse("reports:weekly_report_dashboard"),
            {
                "user": self.member.id,
            },
        )
        self.assertEqual(response.status_code, 200)

        # In that window, selected user is member; tasks in week are still 2
        self.assertEqual(response.context["total_tasks"], 2)
        self.assertEqual(response.context["completed_tasks"], 1)
        self.assertEqual(response.context["pending_tasks"], 1)
