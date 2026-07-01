from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from tasks.models import Task, Project
from tracking.models import DailyLog


class DailyLogCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        self.project = Project.objects.create(
            name="Projet Test",
            description="Description du projet test",
        )

        self.task_todo = Task.objects.create(
            name="Tâche À Faire",
            project=self.project,
            assigned_to=self.user,
            created_by=self.user,
            due_date="2030-01-01",
            status="TODO",
        )
        self.task_inprogress = Task.objects.create(
            name="Tâche En Cours",
            project=self.project,
            assigned_to=self.user,
            created_by=self.user,
            due_date="2030-01-02",
            status="INPROGRESS",
        )
        self.task_done = Task.objects.create(
            name="Tâche Terminée",
            project=self.project,
            assigned_to=self.user,
            created_by=self.user,
            due_date="2030-01-03",
            status="DONE",
        )
        self.task_blocked = Task.objects.create(
            name="Tâche Bloquée",
            project=self.project,
            assigned_to=self.user,
            created_by=self.user,
            due_date="2030-01-04",
            status="BLOCKED",
        )

        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

    def test_log_create_view_uses_correct_template(self):
        response = self.client.get(reverse("tracking:log_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tracking/log_form.html")

    def test_log_create_view_filters_tasks_only_todo_inprogress(self):
        response = self.client.get(reverse("tracking:log_create"))
        form = response.context["form"]

        available_tasks = form.fields["task"].queryset
        self.assertIn(self.task_todo, available_tasks)
        self.assertIn(self.task_inprogress, available_tasks)

        self.assertNotIn(self.task_done, available_tasks)
        self.assertNotIn(self.task_blocked, available_tasks)

    def test_log_create_view_only_own_tasks(self):
        other_user = User.objects.create_user(
            username="otheruser",
            password="testpass123",
        )

        other_task = Task.objects.create(
            name="Tâche Autre Utilisateur",
            project=self.project,
            assigned_to=other_user,
            created_by=other_user,
            due_date="2030-01-05",
            status="TODO",
        )

        response = self.client.get(reverse("tracking:log_create"))
        available_tasks = response.context["form"].fields["task"].queryset
        self.assertNotIn(other_task, available_tasks)

    def test_log_create_post_valid(self):
        data = {
            "task": self.task_todo.id,
            "progress_delta": 50,
            "comment": "Travail en cours",
            "difficulties": "Aucune difficulté",
        }
        response = self.client.post(reverse("tracking:log_create"), data, follow=True)

        self.assertRedirects(response, reverse("tracking:log_list"))
        self.assertEqual(DailyLog.objects.count(), 1)

        log = DailyLog.objects.first()
        self.assertEqual(log.task, self.task_todo)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.progress_delta, 50)

    def test_log_create_post_missing_task_shows_errors(self):
        data = {
            "task": "",
            "progress_delta": 10,
            "comment": "Test",
            "difficulties": "",
        }
        response = self.client.post(reverse("tracking:log_create"), data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(DailyLog.objects.count(), 0)

    def test_log_create_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("tracking:log_create"))
        self.assertEqual(response.status_code, 302)


class DailyLogListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            password="testpass123",
        )

        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        self.project = Project.objects.create(
            name="Projet Test",
            description="Description du projet",
        )

        self.task_user = Task.objects.create(
            name="Tâche 1",
            project=self.project,
            assigned_to=self.user,
            created_by=self.user,
            due_date="2030-02-01",
            status="TODO",
        )
        self.task_other = Task.objects.create(
            name="Tâche 2",
            project=self.project,
            assigned_to=self.other_user,
            created_by=self.other_user,
            due_date="2030-02-02",
            status="TODO",
        )

        self.log1 = DailyLog.objects.create(
            user=self.user,
            task=self.task_user,
            comment="Log 1",
            difficulties="",
            progress_delta=50,
        )
        self.log2 = DailyLog.objects.create(
            user=self.other_user,
            task=self.task_other,
            comment="Log autre",
            difficulties="",
            progress_delta=30,
        )

    def test_log_list_view_uses_correct_template_and_context(self):
        response = self.client.get(reverse("tracking:log_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tracking/log_list.html")

        self.assertIn("logs", response.context)
        self.assertEqual(response.context["logs"].count(), 1)
        self.assertEqual(response.context["logs"].first().user, self.user)

    def test_log_list_admin_sees_all_logs(self):
        self.user.role = "ADMIN"
        self.user.save(update_fields=["role"])

        response = self.client.get(reverse("tracking:log_list"))
        self.assertEqual(response.status_code, 200)

        self.assertIn("logs", response.context)
        self.assertEqual(response.context["logs"].count(), 2)
