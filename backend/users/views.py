from django.shortcuts import render

# Create your views here.
import hashlib
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.utils import timezone

from django_filters import rest_framework as filters
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


from .custom_services import (
    create_token,
    error_payload,
    generate_verification_code,
    success_payload,
)
from .models import Account, Verification
from .serializers import LoginUsersSerializer, UserSerializer


# function to email verification and send code
def email_verification(email, new_email=None):
    try:
        # delete all previous attempts code
        Verification.objects.filter(email=email).delete()
        # Calling generate_verification_code() to genrate random code
        verification_code = str(generate_verification_code())
        # # one way hash the verification code to save it in table to varify later on verification api
        hashed_code = hashlib.blake2s(verification_code.encode()).hexdigest()
        start_datetime = datetime.now(tz=timezone.utc)
        end_datetime = start_datetime + timedelta(minutes=30)
        verify = Verification(
            email=email,
            new_email=new_email,
            code=hashed_code,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
        verify.save()

        # Calling mailSend() from custom package to send emails
        subject = "Colt Verification Code"
        message = (
            """Please use this code to verify. It is valid for 30 mins.
        Verification Code:"""
            + verification_code
            + """ """
        )

        email_from = ""  # settings.EMAIL_HOST_USER
        print("\n\n\n", message, "\n\n\n")
        if new_email:
            recipients_list = [new_email]
        else:
            recipients_list = [email]
        try:
            send_mail(subject, message, email_from, recipients_list)
        except Exception as e:
            pass
    except Exception as e:
        return str(e)


"""User signup APIView view """


class RegisterUser(APIView):
    permission_classes = [
        AllowAny,
    ]

    def post(self, request):
        try:
            username = request.data["username"].lower()
            password = request.data["password"]
            email = request.data["email"].lower()
            first_name = request.data["first_name"]
            last_name = request.data["last_name"]

            if len(username) < 4:
                return Response(
                    error_payload("Username should have atleast 4 characters"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "@" in username or "." in username:
                return Response(
                    error_payload("Invalid username"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "@colt.net" not in email:
                return Response(
                    error_payload("Invalid email address"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if any(char.isalpha() for char in username):
                pass
            else:
                return Response(
                    error_payload("Username should atleast contain one characters"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if len(password) < 8:
                return Response(
                    error_payload("Password should have atleast 8 characters"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # check if email or username  already exists
            if Account.objects.filter(email__iexact=email).exists():
                return Response(
                    error_payload("Email already exists"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if Account.objects.filter(username__iexact=username).exists():
                return Response(
                    error_payload("Username already exists"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            email_verification(email)  # sending verification email

            data = {"msg": f"Verification email sent to {email}"}
            return Response(success_payload(data), status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                error_payload({"error": "400 Bad Request"}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


"""Register email verification APIView"""


class VerifyUser(generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [
        AllowAny,
    ]

    def post(self, request, *args, **kwargs):
        # try:
        if "code" in request.data:
            verification_code = str(request.data["code"])
            email = request.data["email"].lower()

            hashed_code = hashlib.blake2s(verification_code.encode()).hexdigest()

            if not Verification.objects.filter(
                email__iexact=email, code=hashed_code
            ).exists():
                return Response(
                    error_payload("Invalid OTP"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            verify = Verification.objects.filter(
                email__iexact=email, code=hashed_code
            ).first()
            end_time = verify.end_datetime
            now = datetime.now(tz=timezone.utc)

            if now > end_time:
                verify.delete()
                return Response(
                    error_payload("The code has expired. Please try again"),
                    status=status.HTTP_408_REQUEST_TIMEOUT,
                )

            else:
                data = self.request.data
                data.pop("code")
                if "confirmPassword" in data:
                    data.pop("confirmPassword")

                data["username"] = data["username"].lower()
                data["first_name"] = data["first_name"].title()
                data["last_name"] = data["last_name"].title()
                data["email"] = data["email"].lower()
                user = Account.objects.create_user(**data)
                token = create_token(user)
                serializer = self.serializer_class(user, context={"request": request})
                # delete code after verification success or expired
                Verification.objects.filter(email__iexact=email).delete()
                return Response(
                    success_payload(serializer.data, token=token),
                    status=status.HTTP_200_OK,
                )

        else:
            return Response(
                error_payload("code field is required"),
                status=status.HTTP_400_BAD_REQUEST,
            )
        # except Exception as e:
        #     return Response(error_payload("400 Bad Request"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


"""Sign In view with django  rest_framework  ObtainAuthToken"""


class LoginUser(APIView):
    serializer_class = LoginUsersSerializer

    def post(self, request, *args, **kwargs):
        try:
            email = request.data["email"].lower()
            password = request.data["password"]

            if email and password:
                # concatenate password with salt value for authenticate
                user = Account.objects.filter(email__iexact=email).first()
                if not user:
                    return Response(
                        error_payload("Username does not exist"),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not user.is_active:
                    return Response(
                        error_payload("Your account is inactive"),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not user.check_password(password):
                    return Response(
                        error_payload("Invalid password"),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user = authenticate(username=email, password=password)

                if user:
                    user.save()  # Note: why are we saving this?
                    token = create_token(user)
                    serializer = self.serializer_class(
                        user, context={"request": request}
                    )

                    return Response(
                        success_payload(serializer.data, token=token),
                        status=status.HTTP_200_OK,
                    )

                else:
                    return Response(
                        error_payload("Invalid Username or Password"),
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            else:
                return Response(
                    error_payload("username and  password both fields are required"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            print(e)
            return Response(
                error_payload(str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileAPI(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LoginUsersSerializer

    def get(self, request):
        user = self.request.user
        user = Account.objects.filter(username=user.username).first()
        if not user:
            return Response(
                error_payload("Username does not exists"),
                status=status.HTTP_404_NOT_FOUND,
            )
        if not user.is_active:
            return Response(
                error_payload("Your account is inactive"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(user)

        return Response(
            success_payload(serializer.data),
            status=status.HTTP_200_OK,
        )


class LogoutUser(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        context = {}
        # logout(request)
        context["content"] = None
        return Response(context, status.HTTP_204_NO_CONTENT)


# Checking  if the provided email for reset password is vaild and send
# verification code on it


class ForgotPassword(APIView):
    permission_classes = [AllowAny]

    def put(self, request, *args, **kwargs):
        if "email" in request.data:
            email = self.request.data["email"].lower()
            user = Account.objects.filter(email__iexact=email).first()
            if not user:
                return Response(
                    error_payload("Account does not exist"),
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            response = email_verification(email)
            data = {"user_id": user.id}
            return Response(success_payload(data), status=status.HTTP_200_OK)
        else:
            return Response(
                error_payload("email field is required"),
                status=status.HTTP_400_BAD_REQUEST,
            )


class ForgotPasswordOTPVerificationAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            if not "user_id" in request.data:
                return Response(
                    error_payload("User Id required!"),
                    status=status.HTTP_404_NOT_FOUND,
                )

            user_id = request.data["user_id"]

            account = Account.objects.filter(id=user_id).first()
            if not account:
                # raise ObjectDoesNotExist("Account does not exists")
                return Response(
                    error_payload("Account does not exist"),
                    status=status.HTTP_404_NOT_FOUND,
                )

            code = str(request.data["code"])
            email = account.email

            hashed_code = hashlib.blake2s(code.encode()).hexdigest()
            if not Verification.objects.filter(
                email__iexact=email, code=hashed_code
            ).exists():
                return Response(
                    error_payload("Invalid OTP"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            verify = Verification.objects.filter(
                email__iexact=email, code=hashed_code
            ).first()
            end_time = verify.end_datetime
            now = datetime.now(tz=timezone.utc)
            # checking if code is expired
            if now > end_time:
                verify.delete()
                return Response(
                    error_payload("The code has expired. Please try again"),
                    status=status.HTTP_408_REQUEST_TIMEOUT,
                )
            return Response(
                success_payload({"user_id": user_id, "email": email}),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                error_payload(f"{str(e)}"),
                status=status.HTTP_400_BAD_REQUEST,
            )


# ResetPasswordView to set new password after verication
class ResetPassword(APIView):
    def put(self, request, *args, **kwargs):
        try:
            email = request.data["email"].lower()
            password = request.data["new_pwd"]
            cpassword = request.data["pwd_confirm"]
            code = str(request.data["code"])

            # valid password lenght to 8 characters
            if len(password) < 8:
                return Response(
                    error_payload("Password should have atleast 8 characters"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if password != cpassword:
                return Response(
                    error_payload("Password Mismatch"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                # get user object and update password
                hashed_code = hashlib.blake2s(code.encode()).hexdigest()

                if not Verification.objects.filter(
                    email__iexact=email, code=hashed_code
                ).exists():
                    raise ValueError("Invalid OTP")

                verify = Verification.objects.filter(
                    email__iexact=email, code=hashed_code
                ).first()
                end_time = verify.end_datetime
                now = datetime.now(tz=timezone.utc)

                # checking if code is expired
                if now > end_time:
                    verify.delete()
                    return Response(
                        error_payload("The code has expired. Please try again"),
                        status=status.HTTP_408_REQUEST_TIMEOUT,
                    )

                user = Account.objects.filter(email__iexact=email).first()
                user.set_password(password)
                user.save()
                Verification.objects.filter(
                    email__iexact=email, code=hashed_code
                ).delete()
                msg = "password set successfully"
                return Response(
                    success_payload({"user_id": user.id, "msg": msg}),
                    status=status.HTTP_200_OK,
                )
        except Exception as e:
            return Response(error_payload(str(e)), status=status.HTTP_400_BAD_REQUEST)


# Change password after login
class ChangePasswordAPI(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        try:
            old_pwd = request.data["old_pwd"]
            new_pwd = request.data["new_pwd"]
            pwd_confirm = request.data["pwd_confirm"]

            if not request.user.check_password(old_pwd):
                return Response(
                    error_payload("Old password is incorrect"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if len(new_pwd) < 8:
                return Response(
                    error_payload("New Password should have atleast 8 characters"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if new_pwd != pwd_confirm:
                return Response(
                    error_payload("New Password mismatch"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = request.user
            user.set_password(new_pwd)
            user.save()
            return Response(
                success_payload({"user_id": request.user.id}), status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                error_payload("400 Bad Request"), status=status.HTTP_400_BAD_REQUEST
            )


# ForgotUsername
class ForgotUsername(APIView):
    permission_classes = [AllowAny]

    def put(self, request, *args, **kwargs):
        if "email" in request.data:
            email = request.data["email"]
            # Check if provided email is registered or not
            user = Account.objects.filter(email=email).first()
            if not user:
                raise ObjectDoesNotExist("This email address is not registered")

            email_verification(email)
            data = {"user_id": user.id}
            return Response(success_payload(data), status=status.HTTP_200_OK)
        else:
            return Response(
                error_payload("email field is required"),
                status=status.HTTP_400_BAD_REQUEST,
            )


"""Forgot username email Code verification View"""


class VerifyUsername(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # get user_id from verify url kwargs
        user_id = kwargs["user_id"]

        # checking is user exist
        try:
            user = Account.objects.get(id=user_id)
        except Account.DoesNotExist:
            return Response(
                error_payload("User does not exist"), status=status.HTTP_404_NOT_FOUND
            )

        try:
            if "code" in request.data:
                verification_code = request.data["code"]
                hashed_code = hashlib.blake2s(verification_code.encode()).hexdigest()
                try:
                    # get verification object to verify a user code and also
                    # check for expire code
                    verify = Verification.objects.get(
                        email=user.email, code=hashed_code
                    )
                    end_time = verify.end_datetime
                    now = datetime.now(tz=timezone.utc)
                    # checking if code is expired
                    if now > end_time:
                        verify.delete()
                        return Response(
                            error_payload("The code has expired. Please try again"),
                            status=status.HTTP_408_REQUEST_TIMEOUT,
                        )
                    else:
                        # genrate new username and send to user email

                        new_username = user.username
                        message = (
                            """Here is your Username:""" + str(new_username) + """ """
                        )
                        subject = "Colt Forgot Username"
                        recipients_list = [user.email]
                        email_from = settings.EMAIL_HOST_USER
                        try:
                            send_mail(subject, message, email_from, recipients_list)
                        except Exception as e:
                            pass
                        data = {}
                        return Response(
                            success_payload(data), status=status.HTTP_200_OK
                        )
                except Verification.DoesNotExist:
                    return Response(
                        error_payload("Invaild Code"), status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response(
                    error_payload("code field is required"),
                    status=status.HTTP_404_NOT_FOUND,
                )
        except Exception as e:
            return Response(
                error_payload(str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResendOTP(APIView):
    permission_classes = [AllowAny]

    def put(self, request):
        if "email" in request.data:
            email = self.request.data["email"].lower()
            try:
                email_verification(email)
                data = {}
                return Response(success_payload(data), status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    error_payload("400 Bad Request"),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        else:
            return Response(
                error_payload("email field is required"),
                status=status.HTTP_400_BAD_REQUEST,
            )


# view class to get single user data
class UserDetail(APIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id, *args, **kwargs):
        # user_id = kwargs.get("user_id")
        user = Account.objects.filter(id=user_id).first()
        if not user:
            raise ObjectDoesNotExist("User does not exist")
        token = create_token(user)
        data = self.serializer_class(user, context={"request": request}).data
        # del data['']
        return Response(success_payload(data, token=token), status=status.HTTP_200_OK)

    def put(self, request, user_id, *args, **kwargs):
        # user_id = kwargs.get('user_id')
        # new_email = request.data.get('new_email')
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")

        user = Account.objects.filter(id=request.user.id).first()
        if not user:
            raise ObjectDoesNotExist("User does not exists")

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        # if user_image_file:
        #     user.user_image_file = user_image_file

        user.save()
        token = create_token(user)
        serializer = self.serializer_class(user, context={"request": request})
        return Response(
            success_payload(serializer.data, token=token), status=status.HTTP_200_OK
        )


class ChangeEmailVerification(APIView):

    def post(self, request, *args, **kwargs):
        username = request.data["username"]
        new_email = request.data["new_email"].lower()
        email = request.data["email"].lower()
        code = request.data["code"]
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")

        hashed_code = hashlib.blake2s(code.encode()).hexdigest()

        verify = Verification.objects.filter(
            email__iexact=email, new_email=new_email, code=hashed_code
        ).first()

        if not verify:
            raise ObjectDoesNotExist("Email does not exists")
        end_time = verify.end_datetime
        now = datetime.now(tz=timezone.utc)
        # checking if code is expired
        if now > end_time:
            verify.delete()
            return Response(
                error_payload("The code has  expired. Please try again."),
                status=status.HTTP_408_REQUEST_TIMEOUT,
            )

        user = Account.objects.filter(email__iexact=email).first()
        user.email = new_email
        user.username = username
        user.first_name = first_name
        user.last_name = last_name

        user.save()
        # delete code after verification success or expired
        Verification.objects.filter(email__iexact=email).delete()
        return Response(
            success_payload({"user_id": user.id, "email": user.email}),
            status=status.HTTP_200_OK,
        )
