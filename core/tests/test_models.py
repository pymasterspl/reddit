from django.contrib.auth import get_user_model

from core.models import Post, PostVote, Community

User = get_user_model()


def test_score_calculation(self):
    community = Community.objects.create(name="Test community")
    post = Post.objects.create(community=community, title="Test Post", content="This is a test post.")
    post.post_votes.create(user=User.objects.create_user('test_user1@test.com'), type=PostVote.UPVOTE)
    post.post_votes.create(user=User.objects.create_user('test_user2@test.com'), type=PostVote.UPVOTE)
    post.post_votes.create(user=User.objects.create_user('test_user3@test.com'), type=PostVote.DOWNVOTE)

    self.assertEqual(post.score, 1)  # 2 upvotes - 1 downvote
