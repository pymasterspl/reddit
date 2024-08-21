from rest_framework.generics import ListAPIView, RetrieveAPIView
from core.serializers import CommunitySerializer, MinimalCommunitySerializer, PostSerializer
from core.models import Community, Post
from django.shortcuts import get_object_or_404


class CommunitiesAPIList(ListAPIView):
    queryset = Community.objects.all()
    serializer_class = MinimalCommunitySerializer
    # queryset = Community.objects.all()

class CommunityDetailAPIView(RetrieveAPIView):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    lookup_field = "slug"


class PostAPIListView(ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


class CommunityPostsListAPIView(ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = "slug"
    def get_serializer(self, *args, **kwargs):
        
        return super().get_serializer(*args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        # community = Community.objects.get(slug=kwargs["slug"])
        community = get_object_or_404(Community, slug=kwargs["slug"])
        self.queryset = Post.objects.filter(community=community)
        return super().list(request, *args, **kwargs)