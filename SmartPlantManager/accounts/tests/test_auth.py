from django.test import TestCase
from django.urls import reverse
from accounts.models import Utente


class RegistrazioneTest(TestCase):

    def test_registrazione_valida(self):
        r = self.client.post(reverse('register'), {
            'username': 'mario',
            'email': 'mario@test.com',
            'password1': 'Test1234!',
            'password2': 'Test1234!',
        })
        self.assertRedirects(r, reverse('login'))
        self.assertTrue(Utente.objects.filter(username='mario').exists())

    def test_password_senza_numero(self):
        r = self.client.post(reverse('register'), {
            'username': 'mario', 'email': 'mario@test.com',
            'password1': 'solettere!', 'password2': 'solettere!',
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Utente.objects.filter(username='mario').exists())

    def test_password_troppo_corta(self):
        r = self.client.post(reverse('register'), {
            'username': 'mario', 'email': 'mario@test.com',
            'password1': 'Ab1!', 'password2': 'Ab1!',
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Utente.objects.filter(username='mario').exists())

    def test_password_non_coincidono(self):
        r = self.client.post(reverse('register'), {
            'username': 'mario', 'email': 'mario@test.com',
            'password1': 'Test1234!', 'password2': 'Diversa1!',
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Utente.objects.filter(username='mario').exists())

    def test_username_duplicato(self):
        Utente.objects.create_user('mario', 'mario@test.com', 'Test1234!')
        r = self.client.post(reverse('register'), {
            'username': 'mario', 'email': 'altro@test.com',
            'password1': 'Test1234!', 'password2': 'Test1234!',
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Utente.objects.filter(username='mario').count(), 1)

    def test_email_duplicata(self):
        Utente.objects.create_user('mario', 'mario@test.com', 'Test1234!')
        r = self.client.post(reverse('register'), {
            'username': 'luigi', 'email': 'mario@test.com',
            'password1': 'Test1234!', 'password2': 'Test1234!',
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Utente.objects.filter(username='luigi').exists())


class LoginTest(TestCase):

    def setUp(self):
        Utente.objects.create_user('mario', 'mario@test.com', 'Test1234!')

    def test_login_valido(self):
        r = self.client.post(reverse('login'), {
            'username': 'mario', 'password': 'Test1234!',
        })
        self.assertRedirects(r, reverse('home'))

    def test_login_password_errata(self):
        r = self.client.post(reverse('login'), {
            'username': 'mario', 'password': 'Sbagliata1!',
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.wsgi_request.user.is_authenticated)

    def test_login_utente_inesistente(self):
        r = self.client.post(reverse('login'), {
            'username': 'nessuno', 'password': 'Test1234!',
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.wsgi_request.user.is_authenticated)

    def test_redirect_se_gia_loggato(self):
        self.client.login(username='mario', password='Test1234!')
        r = self.client.get(reverse('login'))
        self.assertRedirects(r, reverse('home'))

    def test_logout(self):
        self.client.login(username='mario', password='Test1234!')
        self.client.get(reverse('logout'))
        r = self.client.get(reverse('home'))
        self.assertEqual(r.status_code, 302)

    def test_home_richiede_login(self):
        r = self.client.get(reverse('home'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r['Location'])
