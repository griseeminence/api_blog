from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constants import (
    MAX_LENGTH_CHARACTERS_1, MAX_LENGTH_CHARACTERS_2,
    MAX_LENGTH_CHARACTERS_3, MAX_LIMIT_CHARACTERS, MAX_SCORE, MIN_SCORE
)

USER = 'user'
ADMIN = 'admin'
MODERATOR = 'moderator'

ROLES = [
    (USER, USER),
    (ADMIN, ADMIN),
    (MODERATOR, MODERATOR),
]


class CustomUser(AbstractUser):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        'username',
        max_length=MAX_LENGTH_CHARACTERS_1,
        unique=True,
        validators=[username_validator]
    )
    first_name = models.CharField(
        'first name',
        max_length=MAX_LENGTH_CHARACTERS_1,
        blank=True
    )
    last_name = models.CharField(
        'last name',
        max_length=MAX_LENGTH_CHARACTERS_1,
        blank=True
    )
    email = models.EmailField(
        'email address',
        unique=True
    )
    #
    role = models.CharField(
        'Role',
        choices=ROLES,
        default=USER,
        max_length=MAX_LENGTH_CHARACTERS_1,
        blank=True
    )
    bio = models.TextField(
        'Bio',
        blank=True
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ('id',)

    @property
    def is_user(self):
        return self.role == USER

    @property
    def is_moderator(self):
        return self.role == MODERATOR

    @property
    def is_admin(self):
        return self.role == ADMIN or self.is_superuser or self.is_staff

    def __str__(self):
        return self.username


class Title(models.Model):
    name = models.CharField(
        verbose_name='Name', max_length=MAX_LENGTH_CHARACTERS_2
    )
    year = models.PositiveIntegerField(verbose_name='Year')
    description = models.TextField(verbose_name='Description', blank=True)
    genre = models.ManyToManyField(
        'Genre',
        blank=True,
        related_name='title',
        verbose_name='Genre')
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='title',
        verbose_name='Category')

    class Meta:
        verbose_name = 'Work'
        verbose_name_plural = 'Works'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(
        verbose_name='Category', max_length=MAX_LENGTH_CHARACTERS_2
    )
    slug = models.SlugField(
        verbose_name='Slug',
        unique=True,
        max_length=MAX_LENGTH_CHARACTERS_3)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(
        verbose_name='Genre', max_length=MAX_LENGTH_CHARACTERS_2
    )
    slug = models.SlugField(
        verbose_name='Slug',
        unique=True,
        max_length=MAX_LENGTH_CHARACTERS_3)

    class Meta:
        verbose_name = 'Genre'
        verbose_name_plural = 'Genres'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Review(models.Model):
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        verbose_name='Author', related_name='reviews'
    )
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE,
        verbose_name='Title', related_name='reviews'
    )
    text = models.TextField(
        verbose_name='Text'
    )
    score = models.PositiveIntegerField(
        verbose_name='Grade',
        validators=[
            MinValueValidator(MIN_SCORE), MaxValueValidator(MAX_SCORE)
        ]
    )
    pub_date = models.DateTimeField(
        verbose_name='Publication date', auto_now_add=True, db_index=True
    )

    class Meta:
        verbose_name = 'review'
        verbose_name_plural = 'reviews'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='title_author_unique_name_constraint'
            )
        ]

    def __str__(self):
        return self.text[:MAX_LIMIT_CHARACTERS]


class Comment(models.Model):
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        verbose_name='Author', related_name='comments'
    )
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE,
        verbose_name='Review', related_name='comments'
    )
    text = models.TextField(verbose_name='Текст комментария')
    pub_date = models.DateTimeField(
        verbose_name='Add date', auto_now_add=True
    )

    class Meta:
        verbose_name = 'comment'
        verbose_name_plural = 'Comments'

    def __str__(self):
        return self.text[:MAX_LIMIT_CHARACTERS]
