import time
from django.conf import settings

def generate_agora_token(channel_name, uid=0, expiration_time=3600):
    """
    Generate Agora token for video calling
    You'll need to install agora-token-builder: pip install agora-token-builder
    """
    try:
        from agora_token_builder import RtcTokenBuilder
        
        # These should be in your Django settings
        app_id = getattr(settings, 'AGORA_APP_ID', 'your-agora-app-id')
        app_certificate = getattr(settings, 'AGORA_APP_CERTIFICATE', 'your-agora-certificate')
        
        # Role: 1 for publisher, 2 for subscriber
        role = 1
        
        # Calculate expiration timestamp
        current_timestamp = int(time.time())
        privilege_expired_ts = current_timestamp + expiration_time
        
        token = RtcTokenBuilder.buildTokenWithUid(
            app_id, app_certificate, channel_name, uid, role, privilege_expired_ts
        )
        
        return token
    except ImportError:
        # Fallback for development - return a dummy token
        return f"dummy-token-{channel_name}-{uid}"
    except Exception as e:
        print(f"Error generating Agora token: {str(e)}")
        return f"error-token-{channel_name}"