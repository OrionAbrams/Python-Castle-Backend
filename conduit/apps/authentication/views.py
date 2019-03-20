from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from castle.configuration import configuration
from castle.client import Client
from castle import events


# Same as setting it through Castle.api_secret
configuration.api_secret = '2gkpBVNSZzxYusQqtgFEMzxEBDbD2Nwx'
# For authenticate method you can set failover strategies: allow(default), deny, challenge, throw
configuration.failover_strategy = 'deny'

# Castle::RequestError is raised when timing out in milliseconds (default: 500 milliseconds)
configuration.request_timeout = 1000

# Whitelisted and Blacklisted headers are case insensitive and allow to use _ and - as a separator, http prefixes are removed
# Whitelisted headers
configuration.whitelisted = ['X_HEADER']
# or append to default
configuration.whitelisted = configuration.whitelisted + ['http-x-header']

# Blacklisted headers take advantage over whitelisted elements
configuration.blacklisted = ['HTTP-X-header']
# or append to default
configuration.blacklisted = configuration.blacklisted + ['X_HEADER']

from .renderers import UserJSONRenderer
from .serializers import (
    LoginSerializer, RegistrationSerializer, UserSerializer
)

class RegistrationAPIView(APIView):
    # Allow any user (authenticated or not) to hit this endpoint.
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = RegistrationSerializer

    def post(self, request):
        
        # The create serializer, validate serializer, save serializer pattern
        # below is common and you will see it a lot throughout this course and
        # your own work later on. Get familiar with it.
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = LoginSerializer
    def post(self, request):
        user = request.data.get('user', {})
        print(user)
        # Notice here that we do not call `serializer.save()` like we did for
        # the registration endpoint. This is because we don't actually have
        # anything to save. Instead, the `validate` method on our serializer
        # handles everything we need.
        serializer = self.serializer_class(data=user)

        # if serializer valid returns false, run the castle LOGIN_FAILED event
        if not serializer.is_valid():
            print("invalid credentials")
            print(request.data)
            castle = Client.from_request(request)
            print(castle.context)
            print(castle.tracked)
            # manually entering ip because need to use either ip api in client or geolocation and send it over
            castle.context['ip'] = '73.15.8.132'
            castle.context['client_id'] = user['castle_client_id']
            # manully entered headers for now, but it may not need these headers--seems to get them automatically
            castle.context['headers'] =  {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko",
                "Accept": "text/html",
                "Accept-Language": "en-us,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "Keep-Alive",
                "Content-Length": "122",
                "Content-Type": "application/javascript",
                "Origin": "https://castle.io/",
                "Referer": "https://castle.io/login"
                }
            print(castle.context)
            castle.track({
                'event': events.LOGIN_FAILED,
                'user_id': 'e325bcdd10ad',
                'user_traits': {
                    'email': 'smith@castle.io',
                    'registered_at': '2015-02-23T22:28:55.387Z'
                }
            })

        # if serializer valid returns false, run the castle LOGIN_SUCCEEDED event
        serializer.is_valid(raise_exception=True)
        print("logged in")
        castle = Client.from_request(request)
        print(castle.context)
        print(request.data)
        print(request.data['user']['castle_client_id'])
        print(castle.tracked())
        # manually entering ip because need to use either ip api in client or geolocation and send it over
        castle.context['ip'] = '73.15.8.132'
        castle.context['client_id'] = user['castle_client_id']
        # manully entered headers for now, but it may not need these headers--seems to get them automatically
        castle.context['headers'] =  {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko",
            "Accept": "text/html",
            "Accept-Language": "en-us,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "Keep-Alive",
            "Content-Length": "122",
            "Content-Type": "application/javascript",
            "Origin": "https://castle.io/",
            "Referer": "https://castle.io/login"
            }
        print(castle.context)
        castle.track({
            'event': events.LOGIN_SUCCEEDED,
            'user_id': 'e325bcdd10ad',
            'user_traits': {
                'email': 'smith@castle.io',
                'registered_at': '2015-02-23T22:28:55.387Z'
            }
        })

        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        # There is nothing to validate or save here. Instead, we just want the
        # serializer to handle turning our `User` object into something that
        # can be JSONified and sent to the client.
        serializer = self.serializer_class(request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        user_data = request.data.get('user', {})

        serializer_data = {
            'username': user_data.get('username', request.user.username),
            'email': user_data.get('email', request.user.email),

            'profile': {
                'bio': user_data.get('bio', request.user.profile.bio),
                'image': user_data.get('image', request.user.profile.image)
            }
        }

        # Here is that serialize, validate, save pattern we talked about
        # before.
        serializer = self.serializer_class(
            request.user, data=serializer_data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
   
        return Response(serializer.data, status=status.HTTP_200_OK)

