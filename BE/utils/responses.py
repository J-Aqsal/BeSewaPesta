from rest_framework.response import Response
from .constants import AUTHENTICATION_FAILED_CODE, BAD_REQUEST_CODE, SUCCESS_CODE, SUCCESS_MESSAGE

def successResponse(message=SUCCESS_MESSAGE, code=SUCCESS_CODE, data=None):

    return Response(
        {
            "code": code,
            "success": True,
            "message": message,
            "data": data
        },
        status=code
    )


def errorResponse(message: str, code=BAD_REQUEST_CODE, data=None):

    return Response(
        {
            "code": code,
            "success": False,
            "message": message,
            "data": data
        },
        status=code
    )

def authenticationFailedResponse(message= str, code=AUTHENTICATION_FAILED_CODE, data=None):
    return Response(
        {
            "code": code,
            "success": False,
            "message": message,
            "data": data
        },
        status=code
    )