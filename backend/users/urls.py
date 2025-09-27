from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from . import views


urlpatterns = [
    # signup user
    path("signup", views.RegisterUser.as_view()),
    # email verification
    path("verify", views.VerifyUser.as_view()),
    path("login", views.LoginUser.as_view()),
    path("logout", views.LogoutUser.as_view()),
    path("profile", views.UserProfileAPI.as_view()),
    # Forgot Password
    path("forgot-password", views.ForgotPassword.as_view()),
    # forgot password verification api
    path(
        "verify-otp-forgot-password", views.ForgotPasswordOTPVerificationAPI.as_view()
    ),
    # reset forgot password
    path("reset-password", views.ResetPassword.as_view()),
    # change password after used logged in
    path("change-password", views.ChangePasswordAPI.as_view()),
    # Forgot Username
    path("username", views.ForgotUsername.as_view()),
    path("<int:user_id>/verify-username", views.VerifyUsername.as_view()),
    # Resend OTP
    path("resend-otp", views.ResendOTP.as_view()),
    # Get single user details
    path("<int:user_id>", views.UserDetail.as_view()),
    path("change-email-verify", views.ChangeEmailVerification.as_view()),
    path("refresh-token", TokenRefreshView.as_view(), name="token_refresh"),
]
