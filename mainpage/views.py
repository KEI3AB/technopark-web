from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.db.models import Q

from mainpage.forms import QuestionForm, SettingsForm, RegistrationForm, AnswerForm
from mainpage.models import Question, Answer, Tag, User
from mainpage.mixins import TagsAndMembersMixin
from mainpage.utilts import toggle_vote

import math


@login_required
@require_POST
def vote(request):
    target = request.POST.get('target')
    
    try:
        obj_id = int(request.POST.get('id'))
        value = int(request.POST.get('value'))
    except (TypeError, ValueError):
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if value not in (1, -1):
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    if target == 'question':
        obj = get_object_or_404(Question, id=obj_id)
    elif target == 'answer':
        obj = get_object_or_404(Answer, id=obj_id)
    else:
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    toggle_vote(request.user, obj, value)
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
@require_POST
def mark_correct(request, aid):
    answer = get_object_or_404(Answer, pk=aid)
    question = answer.question

    if not (request.user == question.author or request.user.is_superuser):
        return HttpResponseForbidden("Only question author or superuser can mark answers.")

    is_checked = 'is_correct' in request.POST

    answer.is_correct = is_checked
    answer.save(update_fields=['is_correct'])

    return redirect(request.META.get('HTTP_REFERER', '/'))


class IndexView(TagsAndMembersMixin, TemplateView):
    http_method_names = [ 'get', ]
    template_name = 'mainpage/index.html'
    QUESTIONS_PER_PAGE = 4

    def get_questions(self, tag = None, user = None, search = None):
        question = Question.objects.all()
        if tag:
            tag_obj = Tag.objects.filter(slug=tag).first()
            if tag_obj:
                question = question.filter(tags=tag_obj)
        if user:
            question = question.filter(author=user)
        
        if search:
            words = search.split()
            for word in words:
                question = question.filter(
                    Q(slug__icontains=word) |
                    Q(title__icontains=word) |
                    Q(detailed__icontains=word) |
                    Q(author__username__icontains=word) |
                    Q(tags__slug__icontains=word)
                ).distinct()
        
        return question

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs) 

        tag = self.request.GET.get('tag', None)
        author_slug = self.request.GET.get('author', None)
        author = None
        if author_slug:
            author = User.objects.filter(slug=author_slug).first()
        
        search_query = self.request.GET.get('search', '').strip()
        questions = self.get_questions(tag=tag, user=author, search=search_query).order_by('-id')
        context['search_query'] = search_query
        context['count_questions'] = questions.count()
        context['questions_per_page'] = self.QUESTIONS_PER_PAGE
        context['max_page'] = math.ceil(questions.count() / self.QUESTIONS_PER_PAGE)
        if context['max_page'] <= 0: context['max_page'] = 1

        page = self.request.GET.get('page', 1)
        try: # Защищаемся от выхода за предел страниц и ввод строки
            page = int(page)
            if page < 1:
                page = 1
            elif page > context['max_page']:
                page = context['max_page']
        except:
            page = 1
        context['page'] = page

        # Вычисляем номера страниц, которые нужно показывать
        # Вроде максимально просто сделал
        if context['max_page'] < 6:
            context['pages'] = [i for i in range(1, context['max_page'] + 1)]
        elif page < 4:
            context['pages'] = [i for i in range(1, 5)] + [context['max_page']]
        elif page > (context['max_page'] - 3):
            context['pages'] = [1] + [i for i in range(context['max_page'] - 3, context['max_page'] + 1)]
        else: 
            context['pages'] = [1] + [i for i in range(page - 1, page + 2)] + [context['max_page']]

        if page == 1:
            context["new_questions"] = questions[0:self.QUESTIONS_PER_PAGE]
        else:
            context["new_questions"] = questions[(page - 1) * self.QUESTIONS_PER_PAGE:((page - 1) * self.QUESTIONS_PER_PAGE) + self.QUESTIONS_PER_PAGE]

        # Временная затычка, выводим первые 20 тегов и пользователей
        context['tags_list'], context['members_list'] = self.get_tags_and_members()[:20]

        return context
    
    
    def dispatch(self, request, *args, **kwargs):
        print(request)
        return super(IndexView, self).dispatch(request, *args, **kwargs)
    


class AskView(TagsAndMembersMixin, LoginRequiredMixin, FormView):
    http_method_names = [ 'get', 'post', ]
    template_name = 'mainpage/ask.html'
    form_class = QuestionForm
    success_url = reverse_lazy('mainpage:index')

    def form_valid(self, form):
        question = form.save(commit=False)
        question.author = self.request.user
        question.save()

        tags_list = form.cleaned_data['tags_text']
        tag_objs = []
        for t in tags_list:
            tag_obj, _ = Tag.objects.get_or_create(title=t.strip().lower())
            tag_objs.append(tag_obj)
        question.tags.set(tag_objs)

        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super(AskView, self).get_context_data(**kwargs)
        context['tags_list'], context['members_list'] = self.get_tags_and_members()
        return context
    
    def dispatch(self, request, *args, **kwargs):
        print(request)
        return super(AskView, self).dispatch(request, *args, **kwargs)


class SettingsView(TagsAndMembersMixin, LoginRequiredMixin, FormView):
    http_method_names = [ 'get', 'post']
    template_name = 'mainpage/settings.html'
    form_class = SettingsForm
    success_url = reverse_lazy('mainpage:settings')

    def get_form_kwargs(self): # для заполнения полей инфой о текущем пользователе
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
            kwargs['files'] = self.request.FILES
        return kwargs
    
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        
    def get_context_data(self, **kwargs):
        context = super(SettingsView, self).get_context_data(**kwargs)
        context['tags_list'], context['members_list'] = self.get_tags_and_members()
        return context
    
    def dispatch(self, request, *args, **kwargs):
        print(request)
        return super(SettingsView, self).dispatch(request, *args, **kwargs)
    

class QuestionView(TagsAndMembersMixin, FormView):
    http_method_names = [ 'get', 'post' ]
    template_name = 'mainpage/question.html'
    form_class = AnswerForm
    success_url = reverse_lazy('')
    ANSWERS_PER_PAGE = 4

    def get_object(self):
        slug = self.kwargs.get('slug')
        qid = self.kwargs.get('qid')
        
        if slug:
            question = Question.objects.filter(slug=slug).first()
            if question:
                return question
        
        elif qid > 0:
            return get_object_or_404(Question, pk=qid)
        
        raise Http404("Question not found")

    def get_context_data(self, **kwargs):
        context = super(QuestionView, self).get_context_data(**kwargs)
        question = self.get_object()

        context['question'] = question
        context['question_rating'] = question.rating
        context['user_vote_question'] = question.get_user_vote(self.request.user)

        answers = question.answer_set.select_related('author').all()
        # сортируем от лучших ответов к худшим
        context['answers'] = sorted([(ans, ans.get_user_vote(self.request.user), ans.rating) for ans in answers], key=lambda x: x[2], reverse=True)

        context['count_answers'] = answers.count()
        context['answers_per_page'] = self.ANSWERS_PER_PAGE
        context['max_page'] = math.ceil(answers.count() / self.ANSWERS_PER_PAGE)
        if context['max_page'] <= 0: context['max_page'] = 1

        page = self.request.GET.get('page', 1)
        try:
            page = int(page)
            if page < 1:
                page = 1
            elif page > context['max_page']:
                page = context['max_page']
        except:
            page = 1
        context['page'] = page

        if context['max_page'] < 6:
            context['pages'] = [i for i in range(1, context['max_page'] + 1)]
        elif page < 4:
            context['pages'] = [i for i in range(1, 5)] + [context['max_page']]
        elif page > (context['max_page'] - 3):
            context['pages'] = [1] + [i for i in range(context['max_page'] - 3, context['max_page'] + 1)]
        else: 
            context['pages'] = [1] + [i for i in range(page - 1, page + 2)] + [context['max_page']]

        if page == 1:
            context["best_answers"] = context['answers'][0:self.ANSWERS_PER_PAGE]
        else:
            context["best_answers"] = context['answers'][(page - 1) * self.ANSWERS_PER_PAGE:((page - 1) * self.ANSWERS_PER_PAGE) + self.ANSWERS_PER_PAGE]

        context['tags_list'], context['members_list'] = self.get_tags_and_members()
        return context
    
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            answer = form.save(commit=False)
            answer.author = request.user
            answer.question = self.get_object()
            answer.save()
            return redirect(request.path)
        
        return self.form_invalid(form)


class RegistrationView(TagsAndMembersMixin, FormView):
    http_method_names = [ 'get', 'post', ]
    template_name = 'mainpage/registration.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('mainpage:index')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()  
        return kwargs
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super(RegistrationView, self).get_context_data(**kwargs)
        context['tags_list'], context['members_list'] = self.get_tags_and_members()
        return context
    
    def dispatch(self, request, *args, **kwargs):
        print(request)
        return super(RegistrationView, self).dispatch(request, *args, **kwargs)

class LoginView(TagsAndMembersMixin, LoginView):
    template_name = 'mainpage/login.html'

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        context['tags_list'], context['members_list'] = self.get_tags_and_members()
        return context
