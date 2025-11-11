from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Sum
from mainpage.models import Vote

def toggle_vote(user, obj, value):
    ct = ContentType.objects.get_for_model(obj.__class__)

    with transaction.atomic(): #защита от race condition в БД
        vote = Vote.objects.filter(user=user, content_type=ct, object_id=obj.id).first()

        if not vote:
            Vote.objects.create(user=user, content_type=ct, object_id=obj.id, value=value)
        else:
            if vote.value == value:
                vote.delete()
            else:
                vote.value = value
                vote.save(update_fields=['value'])

        total = Vote.objects.filter(content_type=ct, object_id=obj.id).aggregate(Sum('value'))['value__sum'] or 0

    return total
        
