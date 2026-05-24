from django.contrib.auth import authenticate
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from utils.responses import authenticationFailedResponse, successResponse, errorResponse
from rest_framework import status
from rest_framework.views import APIView

import jwt
import datetime



@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return errorResponse(message="Username and password are required")

        user = authenticate(
            username=username,
            password=password
        )

        if user is None:
            return errorResponse(message="Invalid credentials")

        payload = {
            'user_id': user.id,
            'username': user.username,
            'groups': [
                group.name
                for group in user.groups.all()
            ],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm='HS256'
        )

        return successResponse(data={'token': token})