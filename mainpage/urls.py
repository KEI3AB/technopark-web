from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views
from django.urls import path, include
from mainpage import views

app_name = 'mainpage'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('ask/', views.AskView.as_view(), name='ask'),
    path('question/id/<int:qid>', views.QuestionView.as_view(), name='question_by_id'),
    path('question/<slug:slug>', views.QuestionView.as_view(), name='question_by_slug'),
    path('registration/', views.RegistrationView.as_view(), name='registration'),
    path('logout/', LogoutView.as_view(next_page='mainpage:index'), name='logout'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('vote/', views.vote, name='vote'),
    path('answer/<int:aid>/mark_correct/', views.mark_correct, name='mark_correct'),
]
