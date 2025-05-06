from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('questions/', views.QuestionListView.as_view(), name='question_list'),
    path('answer/<int:question_id>/', views.answer_question, name='answer_question'),
]