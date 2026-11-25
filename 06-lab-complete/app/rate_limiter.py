"""Redis backed sliding-window rate limiter."""
import hashlib
import time
import uuid
from fastapi import HTTPException
from redis.exceptions import RedisError
from app.config import settings
from app.redis_client import r


def check_rate_limit(key: str) -> None:
    now = time.time()
    redis_key = "rate:" + hashlib.sha256(key.encode()).hexdigest()
    member = f"{now}:{uuid.uuid4().hex}"
    script = """
    local key, now, cutoff, member, limit = KEYS[1], tonumber(ARGV[1]), tonumber(ARGV[2]), ARGV[3], tonumber(ARGV[4])
    redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
    local count = redis.call('ZCARD', key)
    if count >= limit then
      local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
      local retry = 60
      if oldest[2] then retry = math.max(1, math.floor(tonumber(oldest[2]) + 60 - now)) end
      return {0, retry}
    end
    redis.call('ZADD', key, now, member)
    redis.call('EXPIRE', key, 65)
    return {1, 0}
    """
    try:
        allowed, retry_after = r.eval(script, 1, redis_key, now, now - 60, member,
                                      max(1, settings.rate_limit_per_minute))
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="Rate limiter unavailable") from exc
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded",
                            headers={"Retry-After": str(retry_after)})
