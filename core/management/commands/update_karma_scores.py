from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import F, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from core.models import Post
from users.models import Profile


class Command(BaseCommand):
    help = "Updating karma scores for every user"

    def handle(self: "Command", *_args: str, **_options: str) -> None:
        date_limit = timezone.now() - timedelta(days=365)

        def karma_subquery(parent_isnull: bool):
            return (
                Post.objects.filter(
                    author_id=OuterRef("user_id"), 
                    created_at__gte=date_limit, 
                    parent__isnull=parent_isnull
                )
                .values("author_id")
                .annotate(karma_score=Sum(F("up_votes") - F("down_votes")))
                .values("karma_score")
            )

        Profile.objects.update(
            post_karma=Coalesce(Subquery(karma_subquery(parent_isnull=True)), 0),
            comment_karma=Coalesce(Subquery(karma_subquery(parent_isnull=False)), 0),
        )