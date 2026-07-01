from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from tasks.models import Project, Task
from tracking.models import DailyLog


class TaskFilterTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            password="testpass123",
        )

        self.project = Project.objects.create(
            name="Projet Test",
            description="Description du projet",
        )

        self.task_todo = Task.objects.create(
            name="Tâche TODO",
            project=self.project,
            assigned_to=self.user,
            created_by=self.user,
            due_date="2030-03-01",
            status="TODO",
        )
        self.task_inprogress = Task.objects.create(
            name="Tâche INPROGRESS",
            project=self.project,
            assigned_to=self.user,
            created_by=self.user,
            due_date="2030-03-02",
            status="INPROGRESS",
        )
        self.task_done = Task.objects.create(
            name="Tâche DONE",
            project=self.project,
            assigned_to=self.user,
            created_by=self.user,
            due_date="2030-03-03",
            status="DONE",
        )
        self.task_blocked = Task.objects.create(
            name="Tâche BLOCKED",
            project=self.project,
            assigned_to=self.user,
            created_by=self.user,
            due_date="2030-03-04",
            status="BLOCKED",
        )
        self.other_user_task = Task.objects.create(
            name="Tâche autre utilisateur",
            project=self.project,
            assigned_to=self.other_user,
            created_by=self.other_user,
            due_date="2030-03-05",
            status="TODO",
        )

        self.client = self.client_class()
        self.client.login(username="testuser", password="testpass123")

    def test_only_todo_and_inprogress_shown_in_create_form(self):
        response = self.client.get(reverse("tracking:log_create"))
        form = response.context["form"]
        queryset = form.fields["task"].queryset

        self.assertIn(self.task_todo, queryset)
        self.assertIn(self.task_inprogress, queryset)
        self.assertNotIn(self.task_done, queryset)
        self.assertNotIn(self.task_blocked, queryset)

    def test_only_own_tasks_shown_in_create_form(self):
        response = self.client.get(reverse("tracking:log_create"))
        form = response.context["form"]
        queryset = form.fields["task"].queryset

        self.assertNotIn(self.other_user_task, queryset)

    def test_log_list_only_user_logs_by_default(self):
        DailyLog.objects.create(
            user=self.user,
            task=self.task_todo,
            comment="log user",
            difficulties="",
            progress_delta=5,
        )
        DailyLog.objects.create(
            user=self.other_user,
            task=self.other_user_task,
            comment="log other",
            difficulties="",
            progress_delta=3,
        )

        response = self.client.get(reverse("tracking:log_list"))
        logs = response.context["logs"]

        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().user, self.user)
