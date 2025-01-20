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
        seatName = body.get('seatName')

        # 检查用户是否已存在
        if User.objects.filter(seatNumber=seatNumber).exists():
            print("User already exists")
            return JsonResponse({"error": "User already exists"}, status=402)

        # 创建新用户
        user = User.objects.create(seatNumber=seatNumber, seatName=seatName)
        user.save()
        users = User.objects.filter(id__in=[0, 1, 2, 3, 4, 5])
        users_dict = {user.seatNumber: user for user in users}
        users_info = []
        for i in range(6):
            if i in users_dict:
                user = users_dict[i]
                users_info.append({
                    "seatNumber": user.seatNumber,
                    "isReady": user.isReady  # 使用数据库中的信息
                })
            else:
                users_info.append({
                    "id": i,
                    "isReady": False  # 假设初始状态为未准备
                })

        return JsonResponse({
            "code": 0,
            "message": "User created successfully",
            "user": {
                "id": user.id,
                "seatNumber": user.seatNumber,
                "seatName": user.seatName,
                "cards": [],  # 假设初始手牌为空
                "isReady": False  # 假设初始状态为未准备
            },
            "users": users_info
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=403)
    except Exception as e:
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)
