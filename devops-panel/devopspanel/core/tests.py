from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Environment, ServiceGroup, ServiceButton, ServiceButtonLink
from devopspanel.dashboard.forms import ServiceButtonForm, GroupForm, EnvironmentForm, CustomUserCreationForm

User = get_user_model()


class DashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(username='admin', password='password')
        self.environment = Environment.objects.create(name="Test Environment", created_by=self.admin_user)
        self.group = ServiceGroup.objects.create(name="Test Group", environment=self.environment,
                                                 created_by=self.admin_user)
        self.button = ServiceButton.objects.create(name="Test Button", url="http://test.com",
                                                   environment=self.environment, created_by=self.admin_user)

    def test_dashboard_view_access(self):
        # Non-logged in user redirected
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

        # Logged in admin access
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Button")


class ServiceButtonFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', password='password')
        self.environment = Environment.objects.create(name="Environment", created_by=self.user)
        self.group = ServiceGroup.objects.create(name="Test Group", environment=self.environment, created_by=self.user)

    def test_service_button_form_valid(self):
        form_data = {
            'name': 'Button 1',
            'url': 'http://example.com',
            'environment': self.environment.id,
            'is_multi_link': False,
        }
        form = ServiceButtonForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_service_button_form_invalid_without_url(self):
        form_data = {
            'name': 'Button 1',
            'environment': self.environment.id,
            'is_multi_link': False,
        }
        form = ServiceButtonForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('url', form.errors)


class GroupFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', password='password')
        self.environment = Environment.objects.create(name="Environment", created_by=self.user)

    def test_group_form_valid(self):
        form_data = {'name': 'Group 1', 'environment': self.environment.id}
        form = GroupForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_group_form_invalid_without_name(self):
        form_data = {'environment': self.environment.id}
        form = GroupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class EnvironmentFormTests(TestCase):
    def test_environment_form_valid(self):
        form_data = {'name': 'Environment 1'}
        form = EnvironmentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_environment_form_invalid_without_name(self):
        form_data = {}
        form = EnvironmentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class EnvironmentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', password='password')

    def test_environment_creation(self):
        environment = Environment.objects.create(name="Environment", created_by=self.user)
        self.assertEqual(environment.name, "Environment")
        self.assertEqual(environment.created_by, self.user)


class ServiceButtonModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', password='password')
        self.environment = Environment.objects.create(name="Environment", created_by=self.user)

    def test_service_button_creation(self):
        button = ServiceButton.objects.create(
            name="Test Button",
            url="http://example.com",
            environment=self.environment,
            created_by=self.user,
        )
        self.assertEqual(button.name, "Test Button")
        self.assertEqual(button.url, "http://example.com")
        self.assertEqual(button.environment, self.environment)


class ServiceButtonLinkModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', password='password')
        self.environment = Environment.objects.create(name="Environment", created_by=self.user)
        self.button = ServiceButton.objects.create(
            name="Test Button",
            url="http://example.com",
            environment=self.environment,
            created_by=self.user,
        )

    def test_service_button_link_creation(self):
        link = ServiceButtonLink.objects.create(
            service_button=self.button,
            name="Link 1",
            url="http://link.com",
            location="VM"
        )
        self.assertEqual(link.name, "Link 1")
        self.assertEqual(link.url, "http://link.com")
        self.assertEqual(link.service_button, self.button)


class CustomUserCreationFormTests(TestCase):
    def test_custom_user_creation_form_valid(self):
        form_data = {
            'username': 'newuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
            'email': 'newuser@example.com'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_custom_user_creation_form_invalid_password_mismatch(self):
        form_data = {
            'username': 'newuser',
            'password1': 'testpassword123',
            'password2': 'wrongpassword',
            'email': 'newuser@example.com'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)


class InfrastructureDataViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(username='admin', password='password')
        self.environment = Environment.objects.create(name="Test Environment", created_by=self.admin_user)
        self.button = ServiceButton.objects.create(name="Test Button", url="http://test.com",
                                                   environment=self.environment, created_by=self.admin_user)

    def test_infrastructure_data_view_no_environment(self):
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('infrastructure_data'))
        self.assertEqual(response.status_code, 400)

    def test_infrastructure_data_view_valid(self):
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('infrastructure_data') + f'?environment={self.environment.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('nodes', data)
        self.assertIn('edges', data)
