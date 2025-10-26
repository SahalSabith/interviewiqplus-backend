from rest_framework import serializers
from .models import UserProfile
import base64
import numpy as np
import face_recognition


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True}
        }

class FaceRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    image = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        try:
            user = UserProfile.objects.get(email=email)
            data['user'] = user
        except UserProfile.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return data

    def create(self, validated_data):
        user = validated_data['user']
        image_data = validated_data['image'].split(',')[1]
        image_bytes = base64.b64decode(image_data)

        from PIL import Image
        from io import BytesIO
        image = Image.open(BytesIO(image_bytes))
        image = np.array(image)

        encodings = face_recognition.face_encodings(image)
        if len(encodings) == 0:
            raise serializers.ValidationError("No face detected")
        user.face_encoding = encodings[0].tobytes()
        user.save()
        return user
