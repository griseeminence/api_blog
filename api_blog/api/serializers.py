from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers

from reviews.constants import EMAIL_MAX_LEN, USERNAME_MAX_LEN
from reviews.models import Category, Comment, CustomUser, Genre, Review, Title

username_validator = UnicodeUsernameValidator()


def not_me_validator(value):
    """
    Prohibiting 'me' in the 'username' field.
    """
    if value.lower() == "me":
        raise ValidationError(
            "Error: Prohibiting 'me' in the 'username' field"
        )


class UsersSerializer(serializers.ModelSerializer):
    """Serializer for CustomUser model."""

    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role')


class SignUpSerializer(serializers.Serializer):
    """Serializer to create a CustomUser class object."""

    username = serializers.CharField(
        max_length=USERNAME_MAX_LEN,
        required=True,
        validators=[not_me_validator, username_validator],
    )
    email = serializers.EmailField(
        max_length=EMAIL_MAX_LEN,
        required=True,
    )

    class Meta:
        model = CustomUser
        fields = (
            'username', 'email'
        )

    def validate(self, data):
        """
        Checking for uniqueness of users during registration.
        Prohibition of identical fields 'username' and 'email' during registration.
        """
        if not CustomUser.objects.filter(
            username=data.get("username"), email=data.get("email")
        ).exists():
            if CustomUser.objects.filter(username=data.get("username")):
                raise serializers.ValidationError(
                    "A user with the same 'username' already exists"
                )

            if CustomUser.objects.filter(email=data.get("email")):
                raise serializers.ValidationError(
                    "A user with the same 'email' already exists"
                )
        return data


class UserGetTokenSerializer(serializers.Serializer):
    """Serialize the CustomUser class when receiving a JWT."""
    username = serializers.RegexField(
        regex=r'[\w.@+-]+',
        max_length=150,
        required=True
    )
    confirmation_code = serializers.CharField(
        max_length=150,
        required=True
    )

    class Meta:
        model = CustomUser
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for the Review model."""
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )
    title = serializers.SlugRelatedField(read_only=True, slug_field='pk')

    class Meta:
        model = Review
        fields = '__all__'

    def validate(self, data):
        """Validation of data during POST request."""
        title_id = self.context['view'].kwargs['title_id']
        author = self.context['request'].user
        if self.context['request'].method == 'POST':
            if Review.objects.filter(title=title_id, author=author).exists():
                raise serializers.ValidationError(
                    'Разрешается оставлять отзыв всего один раз.'
                )
        return data


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model."""
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )
    review = serializers.SlugRelatedField(read_only=True, slug_field='pk')

    class Meta:
        model = Comment
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    """Serializer for Genre model."""
    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    """Title model serializer designed to view."""
    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description',
                  'genre', 'category', 'rating')


class TitleCreateSerializer(serializers.ModelSerializer):
    """Title model serializer designed to add works."""
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True
    )
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug'
    )

    class Meta:
        model = Title
        fields = ('name', 'year', 'description',
                  'genre', 'category')

    def validate_year(self, value):
        """Validation based on the year field."""
        current_year = timezone.now().year
        if value > current_year:
            raise serializers.ValidationError(
                "The year of manufacture cannot be greater than the current year.")
        return value

    def validate_genre(self, genre):
        """Validation based on the genre field."""
        if genre is None:
            raise serializers.ValidationError(
                "The specified genre does not exist.")
        return genre

    def validate_category(self, category):
        """Validation based on the category field."""
        if category is None:
            raise serializers.ValidationError(
                "The specified category does not exist.")
        return category

    def create(self, validated_data):
        """Function of adding a work."""
        genres_data = validated_data.pop('genre')
        title = Title.objects.create(**validated_data)
        title.genre.set(genres_data)
        return title

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['id'] = instance.id
        return representation
