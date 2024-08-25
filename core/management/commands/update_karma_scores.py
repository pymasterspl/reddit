from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Subquery, OuterRef, Sum, F
from django.db.models.functions import Coalesce

from core.models import Post

from users.models import Profile


class Command(BaseCommand):
    help = 'Updating karma score for every user'

    def handle(self, *args, **options):
        date_limit = timezone.now() - timedelta(days=365)
        karma_subquery = (
            Post.objects
            .filter(author_id=OuterRef('user_id'), created_at__gte=date_limit)
            .values('author_id')
            .annotate(karma_score=Sum(F('up_votes') - F('down_votes')))
            .values('karma_score')
        )
        Profile.objects.update(karma_score=Coalesce(Subquery(karma_subquery), 0))
