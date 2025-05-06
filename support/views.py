from django.views.generic import ListView
from django.shortcuts import render, redirect
from .models import Question, Answer
from django.contrib.auth.decorators import login_required

class QuestionListView(ListView):
    model = Question
    template_name = 'support/questions.html'
    context_object_name = 'questions'
    queryset = Question.objects.filter(answered=False)

@login_required
def answer_question(request, question_id):
    question = Question.objects.get(id=question_id)
    if request.method == 'POST':
        text = request.POST.get('answer')
        Answer.objects.create(question=question, text=text, is_admin=True)
        question.answered = True
        question.save()
        return redirect('support:question_list')
    return render(request, 'support/answer.html', {'question': question})