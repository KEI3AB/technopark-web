from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum

from transliterate import translit
import uuid



class DefaultModel(models.Model):
    class Meta:
        abstract = True


    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateField(auto_now_add=True, verbose_name='Время создания', editable=False, null=True)
    updated_at = models.DateField(auto_now=True, verbose_name='Время редактирования', editable=False, null=True)


class User(AbstractUser):
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


    avatar = models.ImageField(upload_to='avatars', null=True, blank=True)
    slug = models.SlugField(max_length=150, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk or not self.slug:
            curr_slug = slugify(translit(self.username, 'ru', reversed=True))
        
            while User.objects.filter(slug=curr_slug).exists():
                random_suffix = uuid.uuid4().hex[:4]
                curr_slug = f"{curr_slug}+{random_suffix}"
        
            self.slug = curr_slug
        
        super().save(*args, **kwargs)


class Vote(models.Model):   
    VALUE_CHOISES = ((1, 'Up'), (-1, 'Down'))

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.SmallIntegerField(choices=VALUE_CHOISES)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user','content_type', 'object_id'], name='unique_vote_per_user_per_object')
        ]



class Question(DefaultModel):
    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'


    slug = models.SlugField(max_length=200, unique=True)
    title = models.CharField(max_length=200)
    detailed = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = models.ManyToManyField('Tag', blank=True, verbose_name='Теги')


    
    def __str__(self):
        return str(self.title)
    
    def save(self, *args, **kwargs):
        if not self.pk or not self.slug: # генерим slug когда объект создается или если у объекта вообще нет slug
            curr_slug = slugify(translit(self.title, 'ru', reversed=True))

            while Question.objects.filter(slug=curr_slug).exists(): #если занят текущий slug
                random_suffix = uuid.uuid4().hex[:4]
                curr_slug = f"{curr_slug}+{random_suffix}"

            self.slug = curr_slug

        return super(Question, self).save(*args, **kwargs)
    
    def get_tags(self):
        return self.tags.all()

    def answers_count(self):
        return self.answer_set.count()
    
    @property
    def rating(self):
        ct = ContentType.objects.get_for_model(self)
        total = Vote.objects.filter(content_type=ct, object_id=self.id).aggregate(Sum('value'))['value__sum']
        return total or 0
    
    def get_user_vote(self, user):
        if not user or not user.is_authenticated:
            return 0
        ct = ContentType.objects.get_for_model(self)
        vote = Vote.objects.filter(user=user, content_type=ct, object_id=self.id).first()

        if vote:
            return vote.value
        return 0


class Answer(DefaultModel):
    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'


    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return "Ответ на вопрос ID=" + str(self.question_id)
    
    @property
    def rating(self):
        cp = ContentType.objects.get_for_model(self)
        total = Vote.objects.filter(content_type=cp, object_id=self.id).aggregate(Sum('value'))['value__sum']
        return total or 0
    
    def get_user_vote(self, user):
        if not user or not user.is_authenticated:
            return 0
        ct = ContentType.objects.get_for_model(self)
        vote = Vote.objects.filter(user=user, content_type=ct, object_id=self.id).first()

        if vote:
            return vote.value
        return 0


class Tag(models.Model):
    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
    

    title = models.CharField(max_length=200, verbose_name='Название тега', unique=True)
    slug = models.SlugField(max_length=200, unique=True)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.title:
            self.title = self.title.strip().lower()

        # Реализовал алгоритм для slug-а, аналогичный тому, что в Question
        # Не уверен, что он тут нужен, поскольку у title есть свойство unique=True
        # Но пускай будет
        if not self.pk or not self.slug:
            curr_slug = slugify(translit(self.title, 'ru', reversed=True))
        
            while Tag.objects.filter(slug=curr_slug).exists():
                random_suffix = uuid.uuid4().hex[:4]
                curr_slug = f"{curr_slug}+{random_suffix}"
        
            self.slug = curr_slug
        
        super().save(*args, **kwargs)
