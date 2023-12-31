import datetime
from django.contrib import admin
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Question(models.Model):
    """
    Represents a question that can be asked in a poll.

    Attributes:
        question_text (str): The text of the question.
        pub_date (datetime): The date and time when the question was published.
        end_date (datetime): The optional end date and time for the question.
    """
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    end_date = models.DateTimeField('date ended', null=True, blank=True)

    @admin.display(
        boolean=True,
        ordering='pub_date',
        description='Published recently?',
    )
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

    def is_published(self):
        now = timezone.localtime(timezone.now())
        return now >= self.pub_date

    def can_vote(self):
        """
        Check if the question is open for voting.

        Returns:
            bool: True if the question is open for voting, False otherwise.
        """
        now = timezone.localtime(timezone.now())
        if self.end_date is None:
            return now >= self.pub_date
        else:
            return self.pub_date <= now <= self.end_date

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text

    @property
    def votes(self):
        return self.vote_set.count()


class Vote(models.Model):
    """Record a choice for a question made by a user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

    @classmethod
    def get_vote(cls, question: Question, user: User):
        """Return the vote by a user for a specific poll question.

        :param question: a Question to get user's vote for
        :param user: a User whose vote to return
        :returns: the user's vote for the requested question, or None if no vote
        """
        if not user or not user.is_authenticated:
            return None
        try:
            return Vote.objects.get(user=user, choice__question=question)
        except Vote.DoesNotExist:
            # no vote yet
            return None

    def __str__(self):
        return f'Vote by {self.user.username} for {self.choice.choice_text}'
