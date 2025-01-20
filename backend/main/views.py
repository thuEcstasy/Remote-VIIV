from django.http import HttpRequest
from django.http import HttpRequest, JsonResponse
from main.models import User
import json
# Create your views here.
def player_login(request: HttpRequest):
    print("yes")
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'})
    try:
        # 解析请求体中的 JSON 数据
        body = json.loads(request.body)
        seatNumber = body.get('seatNumber')
        print(seatNumber)
        seatName = body.get('seatName')

        # 检查用户是否已存在
        if User.objects.filter(seatNumber=seatNumber).exists():
            print("User already exists")
            return JsonResponse({"error": "User already exists"}, status=402)

        # 创建新用户
        user = User.objects.create(seatNumber=seatNumber, seatName=seatName)
        user.save()
        return JsonResponse({"code": 0, "message": "User created successfully", "user_id": user.id}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=403)
    except Exception as e:
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)
