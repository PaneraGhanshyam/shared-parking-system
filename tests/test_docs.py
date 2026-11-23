from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class ApiDocsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_swagger_ui_accessible_without_auth(self):
        response = self.client.get("/api/docs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("swagger-ui", response.content.decode("utf-8").lower())

    def test_schema_accessible_without_auth(self):
        response = self.client.get("/api/schema/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
