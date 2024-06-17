from rest_framework import serializers
from django.contrib.auth.models import User
from api.models import UserProfile, Posts, Comments, Stories


class RegistrationSerializer(serializers.ModelSerializer):

    class Meta:

        model = User

        fields = ["id","username","email","password"]

        read_only_fields = ["id"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    
    
class UserProfileSerializer(serializers.ModelSerializer):

    posts = serializers.SerializerMethodField()
    followers = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()
    block = serializers.SerializerMethodField()

    class Meta:

        model = UserProfile

        exclude = ("user",)

        read_only_fields = ["id", "created_date", "updated_date", "is_active", "posts", "followers", "following", "block"]

    def get_posts(self, instance):
        return instance.user.userpost.count()

    def get_followers(self, instance):
        return instance.followed_by.count()

    def get_following(self, instance):
        return instance.following.count()
    
    def get_block(self, instance):
        return instance.block.count()


class PostSerializer(serializers.ModelSerializer):

    user = serializers.StringRelatedField()
    likes = serializers.SerializerMethodField()
    saves = serializers.SerializerMethodField()

    class Meta:

        model = Posts

        fields = "__all__"

        read_only_fields = ["id", "user", "likes", "saves", "created_date", "updated_date", "is_active"]

    def get_likes(self, instance):
        return instance.likes.count()
    
    def get_saves(self, instance):
        return instance.saves.count()
    
    
class CommentSerializer(serializers.ModelSerializer):

    user = serializers.StringRelatedField()

    class Meta:

        model = Comments

        fields = "__all__"

        read_only_fields = ["id", "post", "user","created_date", "is_active"]

class StorySerializer(serializers.ModelSerializer):

    user = serializers.StringRelatedField()

    class Meta:

        model = Stories

        fields = "__all__"

        read_only_fields = ["id", "user", "created_date", "expiry_date"]

class UserSearchSerializer(serializers.ModelSerializer):

    class Meta:

        model = User
        
        fields = ['id', 'username']



