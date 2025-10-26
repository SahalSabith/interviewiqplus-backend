from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile
from .serializers import UserProfileSerializer
from django.contrib.auth.hashers import check_password

class RegisterUserAPIView(APIView):
    def post(self, request):
        serializer = UserProfileSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "User registered successfully!",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "message": "Registration failed!",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    def post(self, request):
        identifier = request.data.get('identifier')
        password = request.data.get('password')

        if not identifier or not password:
            return Response({"error": "Email/Mobile and password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserProfile.objects.filter(email=identifier).first() or \
                   UserProfile.objects.filter(mobile=identifier).first()

            if not user:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

            if not check_password(password, user.password):
                return Response({"error": "Invalid password."}, status=status.HTTP_401_UNAUTHORIZED)

            return Response({
                "message": "Login successful!",
                "user": {
                    "full_name": user.full_name,
                    "email": user.email,
                    "mobile": user.mobile,
                    "career_interest": user.career_interest,
                    "target_company": user.target_company
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)