from django.shortcuts import render
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils import timezone
from api.serializers import RegistrationSerializer, UserProfileSerializer, PostSerializer, StorySerializer, CommentSerializer, UserSearchSerializer
from api.models import UserProfile, Posts, Stories, Comments
from rest_framework.generics import CreateAPIView, UpdateAPIView, RetrieveAPIView, DestroyAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework import authentication, permissions
from rest_framework import status

# Create your views here.


class SignUpView(CreateAPIView):

    serializer_class = RegistrationSerializer

    queryset = User.objects.all()


class UserProfileUpdateView(UpdateAPIView, RetrieveAPIView):

    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = UserProfileSerializer

    queryset = UserProfile.objects.all()

    def get_queryset(self):
        return UserProfile.objects.filter(user = self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(user = self.request.user)

    def get(self, request, *args, **kwargs):
        # Get the user profile
        user_profile = self.get_object()
        user_profile_serializer = UserProfileSerializer(user_profile)

        # Get posts associated with the user profile
        user_posts = user_profile.user.userpost.all()
        post_serializer = PostSerializer(user_posts, many=True)

        return Response({
            'user_profile': user_profile_serializer.data,
            'user_posts': post_serializer.data
        }, status=status.HTTP_200_OK)


class ProfileListView(ListAPIView):

    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = UserProfileSerializer
    queryset = UserProfile.objects.all()

    def get_queryset(self):
        return UserProfile.objects.all().exclude(user=self.request.user)


class HomeView(APIView):

    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):

        # Fetch the following users and their IDs     
        following_users = self.request.user.profile.following.all()
        following_user_ids = [user.user_id for user in following_users]

        # Fetch posts of the logged-in user and the users they are following
        posts= Posts.objects.filter(user__in=following_user_ids) | Posts.objects.filter(user=self.request.user).order_by("-created_date")
        post_instance = PostSerializer(posts, many=True)
        current_date=timezone.now()

        # Filter stories to include only stories of the logged-in user and the users they are following
        stories = Stories.objects.filter(user_id__in=following_user_ids, expiry_date__gte=current_date) | Stories.objects.filter(user=self.request.user, expiry_date__gte=current_date).order_by("-created_date")
        story_instance = StorySerializer(stories, many=True)

        return Response({
            'posts': post_instance.data,
            'stories': story_instance.data
        }, status=status.HTTP_200_OK)
        

class FollowView(APIView):

    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        id = kwargs.get('pk')
        user_object = UserProfile.objects.get(id=id)

        action = request.POST.get('action')

        if(action == "follow"):
            self.request.user.profile.following.add(user_object)
            return Response({'message': 'Followed successfully'}, status=status.HTTP_200_OK)
        
        elif(action == "unfollow"):
            self.request.user.profile.following.remove(user_object)
            return Response({'message': 'Unfollowed successfully'}, status=status.HTTP_200_OK)
        

class ProfileBlockView(APIView):

    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        id = kwargs.get("pk")
        user_object = UserProfile.objects.get(id=id)

        action = request.POST.get("action")

        if(action == "block"):
            self.request.user.profile.block.add(user_object)

            # Automatically unfollow the user if they are being blocked
            self.request.user.profile.following.remove(user_object)
            # Automatically remove the user from your following list
            user_object.following.remove(self.request.user.profile)

            return Response({'message': 'Blocked successfully'}, status=status.HTTP_200_OK)

        elif(action == "unblock"):
            self.request.user.profile.block.remove(user_object)
            return Response({'message': 'Unblocked successfully'}, status=status.HTTP_200_OK)
        

class PostCreateView(CreateAPIView):

    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = PostSerializer
    queryset = Posts.objects.all()

    def perform_create(self, serializer):
        # Set the user for the post before saving
        serializer.save(user=self.request.user)


class StoryCreateView(CreateAPIView):

    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = StorySerializer
    queryset = Stories.objects.all()

    def perform_create(self, serializer):
        # Set the user for the story before saving
        serializer.save(user=self.request.user)


class PostLikeSaveView(APIView):

    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        id = kwargs.get('pk')
        post_object = Posts.objects.get(id=id)

        action = request.POST.get('action')

        if(action == "like"):
            post_object.likes.add(self.request.user)
            return Response({'message': 'Post liked successfully'}, status=status.HTTP_200_OK)
        
        elif(action == "unlike"):
            post_object.likes.remove(self.request.user)
            return Response({'message': 'Post unliked successfully'}, status=status.HTTP_200_OK)
        
        elif(action == "save"):
            post_object.saves.add(self.request.user)
            return Response({'message': 'Post saved successfully'}, status=status.HTTP_200_OK)
        
        elif(action == "unsave"):
            post_object.saves.remove(self.request.user)
            return Response({'message': 'Post unsaved successfully'}, status=status.HTTP_200_OK)
        

class CommentView(CreateAPIView):

    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = CommentSerializer
    queryset = Comments.objects.all()

    def perform_create(self, serializer):
        # Set the user for the comments before saving
        # Set the post for the comment before saving
        post_id = self.kwargs.get('pk')
        serializer.save(post_id=post_id, user=self.request.user)


class PostDeleteView(DestroyAPIView):

    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = PostSerializer
    queryset = Posts.objects.all()     


class UserSearchAPIView(APIView):

    serializer_class = UserSearchSerializer
    
    def post(self, request, *args, **kwargs):
        query = request.data.get('username', '')  # Assuming the search query is sent in the request body
        if query:
            users = User.objects.filter(username__icontains=query)
            serializer = self.serializer_class(users, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "Search query is missing"}, status=400)
















