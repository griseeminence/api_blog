from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet, CommentViewSet, GenreViewSet,
    GetTokenViewSet, ReviewViewSet, SignupViewSet,
    TitleViewSet, UsersViewSet
)

router = DefaultRouter()

router.register(
    'users',
    UsersViewSet,
    basename='users'
)

router.register(
    r'categories',
    CategoryViewSet,
    basename='categories'
)

router.register(
    r'genres',
    GenreViewSet,
    basename='genres'
)

router.register(
    r'titles',
    TitleViewSet,
    basename='titles'
)

router.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet, basename='reviews'
)

router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet, basename='comments'
)

app_name = 'users'

urlpatterns = [
    path('v1/auth/token/',
         GetTokenViewSet.as_view({'post': 'create'}),
         name='get_token'),
    path('v1/', include(router.urls)),
    path('v1/auth/signup/',
         SignupViewSet.as_view({'post': 'create'}),
         name='signup'),
]
