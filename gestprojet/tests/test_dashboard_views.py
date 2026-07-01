from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from projects.models import Project
from tasks.models import Task
from tracking.models import DailyLog

User = get_user_model()


class DashboardViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            role="MEMBER",
        )
        today = date.today()

        self.project = Project.objects.create(
            name="Projet Test",
            description="desc",
            start_date=today,
            end_date=today,
            status="ONGOING",
            created_by=self.user,
        )

        self.task = Task.objects.create(
            name="Tâche Test",
            description="",
            project=self.project,
            sub_activity=None,
            assigned_to=self.user,
            created_by=self.user,
            priority="MEDIUM",
            due_date=today,
            status="DONE",
        )

        # DailyLog.date is auto_now_add => create then update if needed
        self.log = DailyLog.objects.create(
            user=self.user,
            task=self.task,
            comment="log",
            difficulties="",
            progress_delta=50,
        )

        self.client = Client()

    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_template_used_when_logged_in(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")
        # Basic context sanity
        self.assertIn("tasks_total", response.context)
        self.assertIn("tasks_done", response.context)
        self.assertIn("recent_logs", response.context)
