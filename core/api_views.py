from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveAPIView

from core.models import Community, Post
from core.serializers import CommunitySerializer, MinimalCommunitySerializer, PostSerializer


class CommunitiesAPIList(ListAPIView):
    queryset = Community.objects.exclude(privacy=Community.PRIVATE).order_by("name")
    serializer_class = MinimalCommunitySerializer


class CommunityDetailAPIView(RetrieveAPIView):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    lookup_field = "slug"

    def get_serializer_class(self: "CommunityDetailAPIView") -> CommunitySerializer:
        if self.get_object().privacy == Community.PRIVATE:
            return MinimalCommunitySerializer
        return super().get_serializer_class()


class PostAPIListView(ListAPIView):
    queryset = Post.objects.exclude(community__privacy=Community.PRIVATE).order_by("up_votes")
    serializer_class = PostSerializer


class CommunityPostsListAPIView(ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = "slug"

    def get_queryset(self: "CommunityPostsListAPIView") -> QuerySet[Post]:
        community = get_object_or_404(Community, slug=self.kwargs["slug"])
        if community.privacy == Community.PRIVATE:
            msg = "Private community is not accessible."
            raise PermissionDenied(msg)
        return Post.objects.filter(community=community).order_by("up_votes")
