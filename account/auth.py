import random
import string

from django.conf import settings

from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache
from django.contrib.auth.hashers import make_password

from common.utils import generate_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response

from rest_framework import viewsets
from rest_framework.decorators import action

from .serializers import AccountSerializer
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from .models import *


class AuthenticationViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.filter(is_deleted=False).order_by("-id")
    serializer_class = AccountSerializer
    permission_classes = [AllowAny]
    search_fields = ['email']

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        if request.user.id != user.id:
            return Response({'detail': 'Bạn không có quyền thay đổi thông tin của người khác.'}, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)
    
    @action(detail=False, methods=['POST'], url_path='register')
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        if 'email' not in request.data:
            return Response({'detail': 'Email không để trống.'}, status=status.HTTP_400_BAD_REQUEST)
        if self.queryset.filter(email=request.data['email']).exists():
            return Response({'detail': 'Email đã tồn tại.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'detail': 'Thiếu email hoặc password'}, status=status.HTTP_400_BAD_REQUEST)

        email = str(email).replace(" ", "").lower()
        password = str(password).replace(" ", "")

        try:
            user = self.queryset.get(email=email)
            if not user.is_active:
                return Response({"detail": "Tài khoản đã bị vô hiệu hóa."}, status=status.HTTP_400_BAD_REQUEST)
            if not user.check_password(password):
                return Response({"detail": "Mật khẩu không chính xác."}, status=status.HTTP_400_BAD_REQUEST)

            refresh = RefreshToken.for_user(user)

            return Response({'refresh': str(refresh), 'access': str(refresh.access_token)}, status=status.HTTP_200_OK)
        except Account.DoesNotExist:
            return Response({"detail": "Tài khoản không tồn tại"}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['POST'], url_path='login-sso')
    def login_sso(self, request, *args, **kwargs):
        token = request.data.get('token')
        try:
            idinfo = id_token.verify_oauth2_token(token, Request(), settings.GOOGLE_OAUTH2_CLIENT_ID)

            email = idinfo.get('email')
            name = idinfo.get('name')
            picture = idinfo.get('picture')

            if not email:
                return Response(data={"detail": "Email không được bỏ trống."}, status=status.HTTP_400_BAD_REQUEST)

            user, created = Account.objects.get_or_create(
                email = email,
                is_deleted = False,
                defaults={
                    'full_name': name,
                    'avatar': picture,
                    'password': generate_password(8)
                }
            )

            if not user.is_active:
                return Response(data={"detail": "Tài khoản đã bị vô hiệu hóa vui lòng liên hệ admin."}, status=status.HTTP_400_BAD_REQUEST)

            refresh = RefreshToken.for_user(user)
            return Response({'refresh': str(refresh), 'access': str(refresh.access_token)}, status=status.HTTP_200_OK)

        except ValueError as e:
            print(e)
            return Response({"detail": "Xác thực thất bại."}, status=status.HTTP_400_BAD_REQUEST)

    # TODO: Logout thì xóa token firebase khỏi db 
    @action(detail=False, methods=['POST'], url_path='logout')
    def logout(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
        return Response({"message": "Đăng xuất tài khoản thành công."})
    
    # @action(detail=False, methods=['post'], url_path='send-otp-reset-password')
    # def send_otp_reset_password(self, request, *args, **kwargs):
    #     email = request.data.get('email')

    #     if not email:
    #         return Response({"detail": "Vui lòng nhập địa chỉ email"}, status=status.HTTP_400_BAD_REQUEST)

    #     try:
    #         user_instance = Account.objects.get(email=email, is_deleted=False, is_active=True)
    #     except Exception as e:
    #         logger.error(e)
    #         return Response({"detail": "Không tìm thấy tài khoản"}, status=status.HTTP_400_BAD_REQUEST)
        
    #     otp_code = ''.join(random.choices(string.digits, k=6))

    #     cache.set(key=f"{user_instance.uuid}-otp", value=otp_code, timeout=300)

    #     html_content = f"""
    #     <div style="text-align: center; font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0;">
    #         <h2 style="color: #000;">Mã OTP của bạn</h2>
    #         <p style="font-size: 16px; color: #333; margin-bottom: 20px;">Dùng mã OTP dưới đây để hoàn tất việc đổi mật khẩu:</p>
    #         <p style="font-size: 32px; font-weight: bold; color: #000; margin: 20px 0;">{otp_code}</p>
    #         <p style="font-size: 14px; color: #555;">Mã sẽ có hiệu lực trong <b>5 phút</b>.</p>
    #     </div>
    #     """
    #     send_message_email(
    #         message=html_content,
    #         subject="Mã OTP đổi mật khẩu",
    #         to_mail=[email]
    #     )

    #     return Response({"message": f"Đã gửi OTP qua email {email}"}, status=status.HTTP_200_OK) 
    

    # @action(detail=False, methods=['POST'], url_path='check-otp')
    # def check_otp(self, request, *args, **kwargs):
    #     otp_code_input = request.data.get('otp_code')
    #     email = request.data.get('email')

    #     if not otp_code_input or not email:
    #         return Response({"detail": "Vui lòng điền đầy đủ thông tin"}, status=status.HTTP_400_BAD_REQUEST)
        
    #     try:
    #         user_instance = Account.objects.get(email=email, is_deleted=False, is_active=True)
    #     except Exception as e:
    #         logger.error(e)
    #         return Response({"detail": "Không tìm thấy tài khoản"}, status=status.HTTP_400_BAD_REQUEST)

    #     otp_cache = cache.get(f"{user_instance.uuid}-otp")
    #     if not otp_cache or otp_code_input != otp_cache:
    #         return Response({"detail": "Mã OTP đã hết hạn hoặc không tồn tại"}, status=status.HTTP_400_BAD_REQUEST)
        
    #     return Response({"otp": otp_cache}, status=status.HTTP_200_OK)
    

    # @action(detail=False, methods=['post'], url_path='forgot-password')
    # def forgot_password(self, request, *args, **kwargs):
    #     otp_code_input = request.data.get('otp_code')
    #     email = request.data.get('email')
    #     new_password = request.data.get('new_password')

    #     if not otp_code_input or not email:
    #         return Response({"detail": "Vui lòng điền đầy đủ thông tin."}, status=status.HTTP_400_BAD_REQUEST)
        
    #     try:
    #         user_instance = Account.objects.get(email=email, is_deleted=False, is_active=True)
    #     except Exception as e:
    #         logger.error(e)
    #         return Response({"detail": "Không tìm thấy tài khoản."}, status=status.HTTP_400_BAD_REQUEST)

    #     otp_cache = cache.get(f"{user_instance.uuid}-otp")
    #     if not otp_cache or otp_code_input != otp_cache:
    #         return Response({"detail": "Mã OTP đã hết hạn hoặc không tồn tại."}, status=status.HTTP_400_BAD_REQUEST)
        
    #     if not verify_password(new_password):
    #         return Response({"detail": "Mật khẩu không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST)
        
    #     user_instance.password = make_password(new_password)
    #     user_instance.save()
    #     cache.delete(f"{user_instance.uuid}-otp")

    #     return Response({"message": "Mật khẩu đã được thay đổi thành công."}, status=status.HTTP_200_OK)
