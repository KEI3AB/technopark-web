from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from mainpage.models import User, Question, Answer, Tag


@admin.register(User)
class UserAdmin(UserAdmin):
    # Костыльно вывожу slug, сам он появлятся не хотел
    fieldsets = list(UserAdmin.fieldsets)
    fieldsets.append((None, {'fields': ('slug', 'avatar')}))

    list_display = list(UserAdmin.list_display) + ['slug']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_active', 'created_at', 'updated_at')

    class AnswerInline(admin.TabularInline):
        model = Answer
        extra = 0
    
    inlines = (AnswerInline, )


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'author', 'is_active', 'created_at', 'updated_at')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('title', )