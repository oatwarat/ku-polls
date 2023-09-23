import datetime

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from .models import Question, Choice
from urllib.parse import urlencode
from django.contrib.auth.models import User
import django.test
from django.urls import reverse


def create_question(question_text, days, end_date=None):
    """
    Create a question with the given `question_text`, a pub_date
    offset to now (negative for questions published in the past,
    positive for questions that have yet to be published), and an optional `end_date`.
    """
    pub_date = timezone.now() + timezone.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=pub_date, end_date=end_date)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the
        index page.
        """
        question = create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question],
        )

    def test_future_question(self):
        """Questions in the future aren't displayed on the index page."""
        time = timezone.localtime(timezone.now()) + datetime.timedelta(days=30)
        Question(question_text="Future question.", pub_date=time)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.
        """
        past_question = create_question(question_text="Past question.", days=-30)

        # Ensure only past questions are displayed
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [past_question],
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        question1 = create_question(question_text="Past question 1.", days=-30)
        question2 = create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question2, question1],
        )


class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)

    def test_is_published_with_future_pub_date(self):
        """
        is_published() should return False for a question with a future pub_date.
        """
        future_question = create_question(question_text="Future question.", days=30)
        self.assertIs(future_question.is_published(), False)

    def test_is_published_with_default_pub_date(self):
        """
        is_published() should return True for a question with the default (now) pub_date.
        """
        default_question = create_question(question_text="Default question.", days=0)
        self.assertIs(default_question.is_published(), True)

    def test_is_published_with_past_pub_date(self):
        """
        is_published() should return True for a question with a pub_date in the past.
        """
        past_question = create_question(question_text="Past question.", days=-30)
        self.assertIs(past_question.is_published(), True)

    def test_can_vote_with_no_end_date(self):
        """
        Test that can_vote() returns True when end_date is None, indicating voting is allowed anytime after pub_date.
        """
        question = create_question(question_text="No end date question.", days=-10)
        self.assertIs(question.can_vote(), True)

    def test_can_vote_with_end_date_in_future(self):
        """
        Test that can_vote() returns True when end_date is in the future, indicating voting is allowed.
        """
        future_time = timezone.now() + timezone.timedelta(days=10)
        question = create_question(question_text="Future end date question.", days=-5, end_date=future_time)
        self.assertIs(question.can_vote(), True)

    def test_can_vote_with_end_date_in_past(self):
        """
        Test that can_vote() returns False when end_date is in the past, indicating voting is not allowed.
        """
        past_time = timezone.now() - timezone.timedelta(days=10)
        question = create_question(question_text="Past end date question.", days=-15, end_date=past_time)
        self.assertIs(question.can_vote(), False)

    def test_can_vote_with_end_date_now(self):
        """
        Test that can_vote() returns True when end_date is set to the current date and time, indicating voting is allowed.
        """
        current_time = timezone.now()
        question = create_question(question_text="End date now question.", days=-5,
                                   end_date=current_time + timezone.timedelta(seconds=1))
        self.assertIs(question.can_vote(), True)


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future should return a 302 redirect.
        """
        future_time = timezone.now() + timezone.timedelta(days=5)
        future_question = create_question(question_text='Future question', days=5, end_date=future_time)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


class UserAuthTest(django.test.TestCase):

    def setUp(self):
        # superclass setUp creates a Client object and initializes test database
        super().setUp()
        self.username = "testuser"
        self.password = "FatChance!"
        self.user1 = User.objects.create_user(
            username=self.username,
            password=self.password,
            email="testuser@nowhere.com"
        )
        self.user1.first_name = "Tester"
        self.user1.save()
        pub_date = timezone.now()
        # we need a poll question to test voting
        q = Question.objects.create(question_text="First Poll Question", pub_date=pub_date)
        q.save()
        # a few choices
        for n in range(1, 4):
            choice = Choice(choice_text=f"Choice {n}", question=q)
            choice.save()
        self.question = q

    def test_logout(self):
        """A user can logout using the logout url.

        As an authenticated user,
        when I visit /accounts/logout/
        then I am logged out
        and then redirected to the login page.
        """
        logout_url = reverse("logout")
        # Authenticate the user.
        self.assertTrue(
            self.client.login(username=self.username, password=self.password)
        )
        # Use a POST request to log out.
        response = self.client.post(logout_url)  # Use POST instead of GET
        self.assertEqual(302, response.status_code)
        # Ensure it redirects to the appropriate page.
        self.assertRedirects(response, reverse(settings.LOGOUT_REDIRECT_URL))

    def test_login_view(self):
        """A user can login using the login view."""
        login_url = reverse("login")
        # Can get the login page
        response = self.client.get(login_url)
        self.assertEqual(200, response.status_code)
        # Can login using a POST request
        # usage: client.post(url, {'key1":"value", "key2":"value"})
        form_data = {"username": "testuser",
                     "password": "FatChance!"
                     }
        response = self.client.post(login_url, form_data)
        # after successful login, should redirect browser somewhere
        self.assertEqual(302, response.status_code)
        # should redirect us to the polls index page ("polls:index")
        self.assertRedirects(response, reverse(settings.LOGIN_REDIRECT_URL))

    def test_auth_required_to_vote(self):
        """Authentication is required to submit a vote.

        As an unauthenticated user,
        when I submit a vote for a question,
        then I am redirected to the login page
          or I receive a 403 response (FORBIDDEN)
        """
        vote_url = reverse('polls:vote', args=[self.question.id])

        # what choice to vote for?
        choice = self.question.choice_set.first()
        # the polls detail page has a form, each choice is identified by its id
        form_data = {"choice": f"{choice.id}"}

        # Encode the next parameter and include it in the login URL
        next_param = urlencode({'next': vote_url})
        login_url = f"{reverse('login')}?{next_param}"

        response = self.client.post(vote_url, form_data)

        # should be redirected to the login page with the next parameter included
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, login_url)
