from django.shortcuts import render, get_object_or_404
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView
from rest_framework.response import Response

from geodjangoProject_Server.settings import SECRET_KEY
from users.serializers import UserSerializer
from .models import User, Profile
import jwt, datetime
from django.contrib.gis.geos import Point


# Create your views here.

# register view
class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# login view
class LoginView(APIView):
    def post(self, request):
        # destructure email and password from req
        email = request.data['email']
        password = request.data['password']

        # find user where with email from req
        user = User.objects.filter(email=email).first()

        # if email does not exist, throw error
        if user is None:
            raise AuthenticationFailed('User not found!')

        # decrypt password with check_password and compare with password from req, if not matching throw error
        if not user.check_password(password):
            raise AuthenticationFailed('Password is incorrect!')

        # payload for JWT
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }

        # token uses a secret key. this was exported from .env and imported here using python_decouple
        # no need to decode anymore in below line in new version of PYJWT
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        # login success if reached here
        response = Response()

        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {
            "jwt": token
        }

        return response


# authenticated user view
class UserView(APIView):
    def get(self, request):
        # from req.cookies get JWT value
        token = request.COOKIES.get('jwt')

        # if no token was found in req.cookies, then throw error
        if not token:
            raise AuthenticationFailed("User unauthenticated! No token found!")

        # if token found, decode it to check if it is legit
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("User unauthenticated! Token invalid or expired!")

        # get user with id found in the payload / token
        user = User.objects.filter(id=payload['id']).first()
        serializer = UserSerializer(user)
        return Response(serializer.data)


# logout view
class LogoutView(APIView):
    def post(self, request):
        response = Response()
        # to logout we delete the cookie token
        response.delete_cookie('jwt')
        response.data = {
            "message": "success"
        }

        return response


# update profile location view
class UpdateProfileLocationView(APIView):
    def post(self, request):
        my_location = request.data['location']
        user_id = request.data['user_id']
        response = Response()
        if not my_location:
            response.status_code = 400
            response.data = {
                "message": "No location found"
            }
            return response

        try:
            my_coords = [float(coord) for coord in my_location.split(", ")]
            my_profile = Profile.objects.get(pk=user_id)
            my_profile.last_location = Point(my_coords)
            my_profile.save()

            message = f"Updated {user_id} with {f'POINT({my_location})'}"

            response.status_code = 200
            response.data = {
                "message": message
            }

            return response
        except:
            response.status_code = 400
            response.data = {
                "message": "No profile found with this ID! Could not update profile in DB!"
            }

            return response
