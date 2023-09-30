from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import generic
from django.utils import timezone
from .models import Choice, Question, Vote
from django.urls import reverse
from django.http import Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


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
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:5]


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
        return Question.objects.all()

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

            return question
        except Question.DoesNotExist:
            # Handle the case when the question with the specified ID is not found
            error_message = "This poll does not exist."
            return render(self.request, 'polls/base.html', {'error_message': error_message})

    def get(self, request, *args, **kwargs):
        try:
            question = self.get_object()
        except Http404:
            return redirect('polls:index')

        if question.end_date and question.end_date < timezone.now():
            return HttpResponseRedirect(reverse('polls:index'))

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = context['question']

        if self.request.user.is_authenticated:
            try:
                user_vote = Vote.objects.get(user=self.request.user, choice__question=question)
                context['user_has_voted'] = True
                context['selected_choice'] = user_vote.choice
            except Vote.DoesNotExist:
                context['user_has_voted'] = False

        return context


class ResultsView(generic.DetailView):
    """
    View to display the results of a specific poll question.

    Attributes:
        model (class): The model class associated with this view.
        template_name (str): The template used to render the view.
    """
    model = Question
    template_name = 'polls/results.html'


@login_required
def index(request):
    latest_question_list = Question.objects.order_by('-pub_date')[:5]
    context = {
        'latest_question_list': latest_question_list,
        'user': request.user,  # Include the user in the context
    }
    return render(request, 'polls/index.html', context)


@login_required
def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    selected_choice = None

    # Check if the user has already voted for this question
    if request.user.is_authenticated:
        try:
            selected_choice = Vote.objects.get(user=request.user, choice__question=question).choice
        except Vote.DoesNotExist:
            pass

    return render(request, 'polls/detail.html', {'question': question, 'selected_choice': selected_choice})


def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    user_choice = None
    if request.user.is_authenticated:
        try:
            user_vote = Vote.objects.get(user=request.user, choice__question=question)
            user_choice = user_vote.choice
        except Vote.DoesNotExist:
            pass
    return render(request, 'polls/results.html', {'question': question, 'user_choice': user_choice})


@login_required
def vote(request, question_id):
    """Handles the voting for a question's choices."""
    question = get_object_or_404(Question, pk=question_id)

    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form with an error message.
        return render(request, 'polls/detail.html', {
            'question': question,
        })
    this_user = request.user

    try:
        # Find a vote for this user and this question.
        vote = Vote.objects.get(user=this_user, choice__question=question)
        vote.choice = selected_choice
    except Vote.DoesNotExist:
        # No matching vote - create a new vote.
        vote = Vote(user=this_user, choice=selected_choice)

    vote = Vote.get_vote(question=question, user=this_user)
    if vote:
        vote.choice = selected_choice
    else:
        # create a new vote
        vote = Vote(user=this_user, choice=selected_choice)
    vote.save()
    messages.info(request,
                  f"Your vote for {selected_choice.choice_text} has been recorded.")
    next_url = request.POST.get('next', reverse('polls:results', args=(question.id,)))
    return HttpResponseRedirect(next_url)
