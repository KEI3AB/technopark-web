from mainpage.models import Tag, User
import random


class TagsAndMembersMixin:
    def get_tags(self):
        return Tag.objects.all()
    
    def get_members(self):
        return User.objects.all()
    
    def get_tags_and_members(self):
        tags = list(self.get_tags())
        members = list(self.get_members())

        colors = ['blueviolet', 'brown', 'chartreuse', 'orange', 'red']

        for tag in tags:
            tag.color = random.choice(colors)
        for member in members:
            member.color = random.choice(colors)
        return tags, members