from django.http import JsonResponse


def request_failed(code, info, status_code=400):
    return JsonResponse({
        "code": code,
        "info": info
    }, status=status_code)


def request_success(data={}):
    return JsonResponse({
        "code": 0,
        "info": "Succeed",
        **data
    })


def return_field(obj_dict, field_list):
    for field in field_list:
        assert field in obj_dict, f"Field `{field}` not found in object."

    return {
        k: v for k, v in obj_dict.items()
        if k in field_list
    }

BAD_METHOD = request_failed(-3, "Bad method", 405)
