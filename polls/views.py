from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render
from django.views import generic
from django.utils import timezone
from .models import Choice, Question
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
from django.http import Http404


class IndexView(generic.ListView):
    """
    View to display a list of the latest poll questions.

    Attributes:
        template_name (str): The template used to render the view.
        context_object_name (str): The name used to pass the list of questions to the template.
    """
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be published in the future).

        Returns:
            QuerySet: The list of latest questions.
        """
        return Question.objects.filter(
            pub_date__lte=timezone.now(),
            end_date__isnull=True,
        ).order_by('-pub_date')[:5]


class DetailView(generic.DetailView):
    """
    View to display the details of a specific poll question.

    Attributes:
        model (class): The model class associated with this view.
        template_name (str): The template used to render the view.
    """

    model = Question
    template_name = 'polls/detail.html'

    def get_queryset(self):
        """
        Return the queryset of questions that are allowed to be viewed.

        Returns:
            QuerySet: The list of questions.
        """
        return Question.objects.filter(
            pub_date__lte=timezone.now(),
            end_date__isnull=True,
        )

    def get_object(self, queryset=None):
        """
        Return the Question object based on the current date and end_date.

        Raises:
            Http404: If the question doesn't exist or voting is not allowed for the question.

        Returns:
            Question: The question object.
        """
        try:
            question = super().get_object(queryset=queryset)
            if not question.can_vote():
                raise Http404("Voting for this poll is not allowed.")
            return question
        except Question.DoesNotExist:
            # Handle the case when the question with the specified ID is not found
            messages.error(self.request, "This poll does not exist.")
            return redirect('polls:index')

    def get(self, request, *args, **kwargs):
        try:
            question = self.get_object()
        except Http404:
            # Question with the specified ID does not exist
            messages.error(request, "This poll does not exist.")
            return redirect('polls:index')

        if not question.can_vote():
            messages.error(request, "Voting for this poll is not allowed.")
            return redirect('polls:index')

        return super().get(request, *args, **kwargs)


class ResultsView(generic.DetailView):
    """
    View to display the results of a specific poll question.

    Attributes:
        model (class): The model class associated with this view.
        template_name (str): The template used to render the view.
    """
    model = Question
    template_name = 'polls/results.html'


def index(request):
    latest_question_list = Question.objects.order_by('-pub_date')[:5]
    context = {'latest_question_list': latest_question_list}
    return render(request, 'polls/index.html', context)


def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/detail.html', {'question': question})


def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/results.html', {'question': question})


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
