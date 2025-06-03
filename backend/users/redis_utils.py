import json
import uuid
from datetime import timedelta
import redis
from django.conf import settings

redis_client = redis.Redis(
    host='redis',  
    port=6379,
    db=0,
    decode_responses=False
)

def store_unverified_user(user_data):
    """Store user data in Redis for 24 hours"""
    token = str(uuid.uuid4())
    expiration_time = 24 * 3600
    redis_client.setex(
        name=f"unverified:{token}",
        time=expiration_time,
        value=json.dumps(user_data)
    )
    return token

def get_and_delete_unverified_user(token):
    """Retrieve and delete user data from Redis"""
    data = redis_client.get(f"unverified:{token}")
    if data:
        redis_client.delete(f"unverified:{token}")
        return json.loads(data)
    return None