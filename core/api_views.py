from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.exceptions import PermissionDenied
from core.serializers import CommunitySerializer, MinimalCommunitySerializer, PostSerializer
from core.models import Community, Post
from django.shortcuts import get_object_or_404


class CommunitiesAPIList(ListAPIView):
    queryset = Community.objects.exclude(privacy=Community.PRIVATE)
    serializer_class = MinimalCommunitySerializer
    

class CommunityDetailAPIView(RetrieveAPIView):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.get_object().privacy == Community.PRIVATE:
            return MinimalCommunitySerializer
        return super().get_serializer_class()

class PostAPIListView(ListAPIView):
    queryset = Post.objects.exclude(community__privacy=Community.PRIVATE)
    serializer_class = PostSerializer


class CommunityPostsListAPIView(ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = "slug"
    
    def list(self, request, *args, **kwargs):
        # community = Community.objects.get(slug=kwargs["slug"])
        community = get_object_or_404(Community, slug=kwargs["slug"])
        if community.privacy == Community.PRIVATE:
            raise PermissionDenied("Private community is not accessible.")
        self.queryset = Post.objects.filter(community=community)
        return super().list(request, *args, **kwargs)