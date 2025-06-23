"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from asgiref.sync import sync_to_async
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
# from firebase_admin import credentials, initialize_app

# Thiết lập biến môi trường cho settings của Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Khởi tạo Django trước khi import các module phụ thuộc
django.setup()

# Import hàm khởi tạo dữ liệu và routing WebSocket sau khi Django setup
from common.scripts import init_db, service_message
from . import routing

# # Khởi tạo Firebase
# try:
#     cred = credentials.Certificate('path/to/your/firebase-adminsdk.json')
#     firebase_app = initialize_app(cred)
#     print("Firebase initialized successfully")
# except Exception as e:
#     print(f"Failed to initialize Firebase: {e}")

# Lấy ứng dụng ASGI của Django
django_app = get_asgi_application()

# Định nghĩa hàm xử lý lifespan
async def handle_lifespan(scope, receive, send):
    if scope['type'] == 'lifespan':
        while True:
            message = await receive()
            if message['type'] == 'lifespan.startup':
                print("[ASGI] 🚀 Đang khởi động...")
                print(service_message("TCS"))
                try:
                    await sync_to_async(init_db)()
                    print("Khởi tạo dữ liệu thành công.")
                    await send({'type': 'lifespan.startup.complete'})
                except Exception as e:
                    print(f"Lỗi khi khởi tạo dữ liệu: {e}")
                    await send({'type': 'lifespan.startup.failed', 'message': str(e)})
            elif message['type'] == 'lifespan.shutdown':
                print("[ASGI] 🛑 Đang tắt...")
                print(service_message("BYE BYE!!!"))
                await send({'type': 'lifespan.shutdown.complete'})
                break

# Tạo ứng dụng ASGI với hỗ trợ WebSocket
application = ProtocolTypeRouter({
    'http': django_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(routing.websocket_urlpatterns)
        )
    ),
    'lifespan': handle_lifespan,
})
