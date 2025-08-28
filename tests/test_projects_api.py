"""
Unit tests for the Projects API endpoints.
"""

from django.urls import reverse

from rest_framework import status

from tasks.models import Project

from .test_base import BaseAPITestCase


class ProjectAPITestCase(BaseAPITestCase):
    """Test cases for Project API endpoints."""

    def test_project_list_get(self):
        """Test retrieving list of projects."""
        # Create additional test project
        project2 = Project.objects.create(name="Second Project", description="Second test project")

        url = reverse("project-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Including self.test_project from setUp

        project_names = [project["name"] for project in response.data]
        self.assertIn("Test Project", project_names)
        self.assertIn("Second Project", project_names)

    def test_project_list_empty(self):
        """Test retrieving empty project list."""
        # Delete the project created in setUp
        Project.objects.all().delete()

        url = reverse("project-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_project_create_success(self):
        """Test creating a new project successfully."""
        url = reverse("project-list-create")
        data = {"name": "New Test Project", "description": "This is a new test project"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Test Project")
        self.assertEqual(response.data["description"], "This is a new test project")

        # Verify project was created in database
        self.assertEqual(Project.objects.filter(name="New Test Project").count(), 1)

    def test_project_create_without_description(self):
        """Test creating a project without description."""
        url = reverse("project-list-create")
        data = {"name": "Project Without Description"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Project Without Description")
        self.assertIsNone(response.data["description"])

    def test_project_create_invalid_data(self):
        """Test creating a project with invalid data."""
        url = reverse("project-list-create")
        data = {"description": "Project without name"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_project_create_empty_name(self):
        """Test creating a project with empty name."""
        url = reverse("project-list-create")
        data = {"name": "", "description": "Project with empty name"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_project_detail_get(self):
        """Test retrieving a specific project."""
        url = reverse("project-detail", kwargs={"pk": self.test_project.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Project")
        self.assertEqual(response.data["id"], self.test_project.id)
        self.assertEqual(response.data["description"], "A test project")

    def test_project_detail_not_found(self):
        """Test retrieving a non-existent project."""
        url = reverse("project-detail", kwargs={"pk": 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_project_update_put(self):
        """Test updating a project with PUT."""
        url = reverse("project-detail", kwargs={"pk": self.test_project.id})
        data = {"name": "Updated Project Name", "description": "Updated project description"}

        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Project Name")
        self.assertEqual(response.data["description"], "Updated project description")

        # Verify project was updated in database
        self.test_project.refresh_from_db()
        self.assertEqual(self.test_project.name, "Updated Project Name")
        self.assertEqual(self.test_project.description, "Updated project description")

    def test_project_update_patch(self):
        """Test partially updating a project with PATCH."""
        original_description = self.test_project.description

        url = reverse("project-detail", kwargs={"pk": self.test_project.id})
        data = {"name": "Patched Project Name"}

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Patched Project Name")
        self.assertEqual(response.data["description"], original_description)  # Should remain unchanged

        # Verify project was updated in database
        self.test_project.refresh_from_db()
        self.assertEqual(self.test_project.name, "Patched Project Name")
        self.assertEqual(self.test_project.description, original_description)

    def test_project_delete(self):
        """Test deleting a project."""
        # Create a new project for deletion (keep test_project for other tests)
        project_to_delete = Project.objects.create(name="Project to Delete", description="This project will be deleted")

        url = reverse("project-detail", kwargs={"pk": project_to_delete.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify project was deleted from database
        with self.assertRaises(Project.DoesNotExist):
            Project.objects.get(id=project_to_delete.id)

    def test_project_delete_with_tasks(self):
        """Test deleting a project that has associated tasks."""
        # Create a task associated with the project
        task = self.create_test_task(project=self.test_project)

        url = reverse("project-detail", kwargs={"pk": self.test_project.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify project was deleted (this should cascade to tasks due to FK relationship)
        with self.assertRaises(Project.DoesNotExist):
            Project.objects.get(id=self.test_project.id)

    def test_project_serialization_fields(self):
        """Test that project serialization includes all expected fields."""
        url = reverse("project-detail", kwargs={"pk": self.test_project.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = ["id", "name", "description"]

        for field in expected_fields:
            self.assertIn(field, response.data)

    def test_project_name_max_length(self):
        """Test project name maximum length validation."""
        url = reverse("project-list-create")

        # Create a name longer than 200 characters (model max_length)
        long_name = "x" * 201

        data = {"name": long_name, "description": "Project with very long name"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
