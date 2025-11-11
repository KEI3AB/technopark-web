import typing as t

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from mainpage.models import Question, User


FAKE_QUESTION_DETAILED = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""


class Command(BaseCommand):
    help = 'Генерация сущностей по модели Вопроса'


    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=100)


    def get_exist_user(self) -> t.Optional[User]:
        return User.objects.filter(is_superuser=True).first()

    def handle(self, *args, **options):
        count = options.get('count')
        count_exist_questions = Question.objects.all().count()
        questions_to_create = []
        author=self.get_exist_user()
        if not author:
            self.stderr.write(self.style.ERROR('нет юзеров в бд\n'))
            return
        
        for n in range(count):
            questions_to_create.append(Question(
                title=f"Вопрос под номером #{count_exist_questions + n + 1}",
                slug=str(slugify(Question.objects.values_list('slug', flat=True))) + f"{n}",
                detailed=FAKE_QUESTION_DETAILED,
                author=author
            ))

        Question.objects.bulk_create(questions_to_create, batch_size=100) # ограничиваем размер запроса для запроси из бд
        print("Было создано вопросов: ", len(questions_to_create))