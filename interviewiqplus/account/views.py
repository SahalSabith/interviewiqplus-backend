from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile
from .serializers import UserProfileSerializer, FaceRegisterSerializer
from django.contrib.auth.hashers import check_password
import numpy as np
import face_recognition
import base64
from PIL import Image
from io import BytesIO

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
        

class RegisterFaceView(APIView):
    def post(self, request):
        serializer = FaceRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Face registered successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyFaceView(APIView):
    def post(self, request):
        import numpy as np
        import base64
        from PIL import Image
        from io import BytesIO
        import face_recognition

        email = request.data.get('email')
        image_data = request.data.get('image').split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        image = np.array(image)

        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        encodings = face_recognition.face_encodings(image)
        if len(encodings) == 0:
            return Response({"error": "No face detected"}, status=400)

        live_encoding = encodings[0]

        stored_encoding = np.frombuffer(user.face_encoding, dtype=np.float64)
        if stored_encoding.shape[0] != 128:
            return Response({"error": "Stored encoding invalid or corrupted"}, status=400)

        result = face_recognition.compare_faces([stored_encoding], live_encoding)

        return Response({"verified": bool(result[0])})