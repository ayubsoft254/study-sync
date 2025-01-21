# views.py
from agora_token_builder import RtcTokenBuilder
import time
import random
from django.conf import settings

from django.http import JsonResponse

def generate_agora_token(request, channel_name):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    appID = settings.AGORA_APP_ID
    appCertificate = settings.AGORA_APP_CERTIFICATE
    uid = random.randint(1, 230)
    expirationTime = 3600  # Token expires in 1 hour
    currentTimestamp = int(time.time())
    privilegeExpiredTs = currentTimestamp + expirationTime
    
    token = RtcTokenBuilder.buildTokenWithUid(
        appID, appCertificate, channel_name, uid, 1, privilegeExpiredTs
    )
    
    return JsonResponse({
        'token': token,
        'uid': uid,
        'channel': channel_name
    })