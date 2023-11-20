from django.conf import settings
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from .filters import TitleFilter
from .mixins import CreateListDestroyViewSet
from .permissions import (AuthorOrReadOnlyPermission, IsAdmin,
                          IsAdminOrReadOnly, ReadOnlyPermission)
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, ReviewSerializer,
                          SignUpSerializer, TitleCreateSerializer,
                          TitleReadSerializer, UserGetTokenSerializer,
                          UsersSerializer)
from reviews.constants import TITLE_NAME_MAX_LEN
from reviews.models import Category, CustomUser, Genre, Review, Title


def send_conf_code(email, confirmation_code):
    """Additional function for SignupViewSet."""
    send_mail(
        subject='Регистрация на сайте Yamdb.com',
        message=f'Код подтверждения: {confirmation_code}',
        from_email=settings.TEST_EMAIL,
        recipient_list=(email,)
    )


class SignupViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """ViewSet of new user registration."""
    queryset = CustomUser.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = (AllowAny,)

    def create(self, request):
        """
        Create a user (CustomUser), then send the confirmation code
        to the e-mail in your profile.
        """

        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, _ = CustomUser.objects.get_or_create(**serializer.validated_data)
        confirmation_code = default_token_generator.make_token(user)

        send_conf_code(
            email=user.email,
            confirmation_code=confirmation_code
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class UsersViewSet(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   viewsets.GenericViewSet):
    """Viewset for User model objects."""

    queryset = CustomUser.objects.all()
    serializer_class = UsersSerializer
    permission_classes = (IsAuthenticated, IsAdmin,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    @action(
        detail=False,
        methods=['get', 'patch', 'delete'],
        url_path=r'([\w.@+-]+)',
        url_name='get_user',
        permission_classes=(IsAdmin,)
    )
    def get_username_info(self, request, username):
        """
        Retrieves information about the user from the 'username'
        field with the ability to edit.
        """
        user = get_object_or_404(CustomUser, username=username)
        if request.method == 'PATCH':
            serializer = UsersSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = UsersSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get', 'patch'],
        url_path='me',
        url_name='me',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def get_data_for_me(self, request):
        """
        Receives information about itself with the possibility
        of partial change via patch.
        """
        if request.method == 'PATCH':
            serializer = UsersSerializer(
                request.user,
                data=request.data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(role=request.user.role)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UsersSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetTokenViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Receiving a JWT token with verification."""
    queryset = CustomUser.objects.all()
    serializer_class = UserGetTokenSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = UserGetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        confirmation_code = serializer.validated_data.get('confirmation_code')
        user = get_object_or_404(CustomUser, username=username)
        if not default_token_generator.check_token(user, confirmation_code):
            message = {'confirmation_code': 'Неверный код подтверждения'}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
        message = {'token': str(AccessToken.for_user(user))}
        return Response(message, status=status.HTTP_200_OK)


class TitleViewSet(viewsets.ModelViewSet):
    """ViewSet of Title model."""
    queryset = Title.objects.order_by('id').annotate(
        rating=Avg('reviews__score'))
    permission_classes = [IsAdminOrReadOnly, ]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter
    pagination_class = LimitOffsetPagination

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        if 'name' in serializer.validated_data and (
                len(
                    serializer.validated_data['name']
                ) > TITLE_NAME_MAX_LEN
        ):
            return Response(
                {"name": [("Название произведения не может",
                           " быть длиннее 256 символов.")]},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_update(serializer)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return TitleReadSerializer
        return TitleCreateSerializer


class CategoryViewSet(CreateListDestroyViewSet):
    """ViewSet of Category model."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly, ]
    lookup_field = 'slug'
    filter_backends = (DjangoFilterBackend,)
    search_fields = ('name')
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        return queryset


class GenreViewSet(CreateListDestroyViewSet):
    """ViewSet of Genre model."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly, ]
    lookup_field = 'slug'
    filter_backends = (DjangoFilterBackend,)
    search_fields = ('name')
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        return queryset


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet Review model."""
    serializer_class = ReviewSerializer
    permission_classes = (AuthorOrReadOnlyPermission,)
    pagination_class = LimitOffsetPagination
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_permissions(self):
        if self.action == 'retrieve':
            return (ReadOnlyPermission(),)
        return super().get_permissions()

    def get_queryset(self):
        title_id = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        return title_id.reviews.all()

    def perform_create(self, serializer):
        title_id = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title_id)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet of Comment modeld."""
    serializer_class = CommentSerializer
    permission_classes = (AuthorOrReadOnlyPermission,)
    pagination_class = LimitOffsetPagination
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_permissions(self):
        if self.action == 'retrieve':
            return (ReadOnlyPermission(),)
        return super().get_permissions()

    def get_queryset(self):
        review_id = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        return review_id.comments.all()

    def perform_create(self, serializer):
        review_id = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        serializer.save(author=self.request.user, review=review_id)
