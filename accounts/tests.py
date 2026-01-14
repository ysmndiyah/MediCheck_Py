from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import BMIResult, WeeklyMealPlan, MentalHealthLog
from datetime import date


class MediCheckTestCase(TestCase):

    def setUp(self):
        """Setup awal sebelum tiap test"""
        self.client = Client()

        self.user = User.objects.create_user(
            username="user@test.com",
            email="user@test.com",
            password="password123"
        )

        self.admin = User.objects.create_user(
            username="admin@test.com",
            email="admin@test.com",
            password="admin123",
            is_staff=True
        )

    # ================= LOGIN =================
    def test_login_user(self):
        response = self.client.post(reverse('accounts:login'), {
            'email': 'user@test.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)

    # ================= BMI =================
    def test_bmi_calculation_and_save(self):
        self.client.login(username="user@test.com", password="password123")

        response = self.client.post(reverse('accounts:bmi'), {
            'berat': 60,
            'tinggi': 160,
            'penyakit': 'tidak ada'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(BMIResult.objects.count(), 1)

    # ================= DASHBOARD =================
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_logged_in(self):
        self.client.login(username="user@test.com", password="password123")
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)

    # ================= WEEKLY MEAL PLAN =================
    def test_weekly_meal_plan_create(self):
        self.client.login(username="user@test.com", password="password123")

        response = self.client.post(reverse('accounts:weekly_meal'), {
            'kondisi_kesehatan': 'asma',
            'alergi_makanan': 'seafood'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(WeeklyMealPlan.objects.count(), 1)

    # ================= MENTAL HEALTH =================
    def test_mental_health_log_save(self):
        self.client.login(username="user@test.com", password="password123")

        response = self.client.post(reverse('accounts:monitor'), {
            'score': 5,
            'kondisi': 'cukup stabil'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MentalHealthLog.objects.count(), 1)

    # ================= ADMIN DASHBOARD =================
    def test_admin_dashboard_access(self):
        self.client.login(username="admin@test.com", password="admin123")
        response = self.client.get(reverse('accounts:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
