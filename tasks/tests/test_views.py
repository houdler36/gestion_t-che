from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from datetime import date

from tasks.models import Task, Project

User = get_user_model()


class TaskViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="adminpass123",
        )

        # Dans ton code, l’accès admin côté task_list dépend de user.role
        # (pas des permissions is_superuser).
        self.admin_user.role = "ADMIN"
        self.admin_user.save(update_fields=["role"])

        self.project = Project.objects.create(
            name="Projet Test",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            created_by=self.user,
        )

        self.task1 = Task.objects.create(
            name="Tâche 1",
            project=self.project,
            assigned_to=self.user,
            created_by=self.user,
            due_date="2030-01-10",
            status="TODO",
        )
        self.task2 = Task.objects.create(
            name="Tâche 2",
            project=self.project,
            assigned_to=self.user,
            created_by=self.user,
            due_date="2030-01-11",
            status="INPROGRESS",
        )

        self.client = Client()

    def test_my_tasks_view(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("tasks:my_tasks"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/my_tasks.html")

    def test_task_list_view_admin_sees_all_tasks(self):
        other_user = User.objects.create_user(
            username="otheruser",
            password="testpass123",
        )
        other_task = Task.objects.create(
            name="Tâche autre user",
            project=self.project,
            assigned_to=other_user,
            created_by=other_user,
            due_date="2030-01-12",
            status="TODO",
        )

        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(reverse("tasks:task_list"))
        self.assertEqual(response.status_code, 200)

        tasks = response.context["tasks"]
        self.assertIn(self.task1, tasks)
        self.assertIn(self.task2, tasks)
        self.assertIn(other_task, tasks)

    def test_task_list_view_non_admin_sees_only_assigned_to(self):
        other_user = User.objects.create_user(
            username="otheruser2",
            password="testpass123",
        )
        other_task = Task.objects.create(
            name="Tâche autre user",
            project=self.project,
            assigned_to=other_user,
            created_by=other_user,
            due_date="2030-01-13",
            status="TODO",
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("tasks:task_list"))
        self.assertEqual(response.status_code, 200)

        tasks = response.context["tasks"]
        self.assertIn(self.task1, tasks)
        self.assertIn(self.task2, tasks)
        self.assertNotIn(other_task, tasks)
