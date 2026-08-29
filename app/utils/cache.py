"""
Кэширование + Rate Limiting + Статистика
"""
import json
import time
from typing import Any, Optional, Dict
from functools import wraps
from threading import Lock

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# === СТАТИСТИКА КЭША ===
class CacheStats:
    """Сбор статистики кэша"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self._lock = Lock()
    
    def record_hit(self):
        with self._lock:
            self.hits += 1
    
    def record_miss(self):
        with self._lock:
            self.misses += 1
    
    def record_set(self):
        with self._lock:
            self.sets += 1
    
    def record_delete(self):
        with self._lock:
            self.deletes += 1
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            
            return {
                "hits": self.hits,
                "misses": self.misses,
                "sets": self.sets,
                "deletes": self.deletes,
                "total_requests": total,
                "hit_rate_percent": round(hit_rate, 2),
                "efficiency": "excellent" if hit_rate > 80 else "good" if hit_rate > 50 else "poor"
            }
    
    def reset(self):
        with self._lock:
            self.hits = 0
            self.misses = 0
            self.sets = 0
            self.deletes = 0

cache_stats = CacheStats()

# === IN-MEMORY КЭШ ===
class SimpleCache:
    def __init__(self):
        self._cache = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            item = self._cache.get(key)
            if not item:
                cache_stats.record_miss()
                return None
            
            if item['expires'] and time.time() > item['expires']:
                self.delete(key)
                cache_stats.record_miss()
                return None
            
            cache_stats.record_hit()
            return item['value']
    
    def set(self, key: str, value: Any, ttl: int = 300):
        with self._lock:
            expires = time.time() + ttl if ttl else None
            self._cache[key] = {
                'value': value,
                'expires': expires
            }
            cache_stats.record_set()
    
    def delete(self, key: str):
        with self._lock:
            self._cache.pop(key, None)
            cache_stats.record_delete()
    
    def clear(self):
        with self._lock:
            self._cache.clear()

# Инициализация
if REDIS_AVAILABLE:
    try:
        redis_client = redis.from_url(
            'redis://localhost:6379/0',
            decode_responses=True,
            socket_timeout=2,
            socket_connect_timeout=2
        )
        redis_client.ping()
        print("✅ Redis connected!")
    except:
        redis_client = None
        print("️  Redis not available. Using in-memory cache.")
else:
    redis_client = None

simple_cache = SimpleCache()

# === ФУНКЦИИ КЭШИРОВАНИЯ ===

def cache_get(key: str) -> Optional[Any]:
    if redis_client:
        try:
            data = redis_client.get(key)
            result = json.loads(data) if data else None
            if result:
                cache_stats.record_hit()
            else:
                cache_stats.record_miss()
            return result
        except:
            cache_stats.record_miss()
            pass
    
    return simple_cache.get(key)

def cache_set(key: str, value: Any, ttl: int = 300):
    if redis_client:
        try:
            redis_client.setex(key, ttl, json.dumps(value))
            cache_stats.record_set()
            return
        except:
            pass
    
    simple_cache.set(key, value, ttl)

def cache_delete(key: str):
    if redis_client:
        try:
            redis_client.delete(key)
            cache_stats.record_delete()
            return
        except:
            pass
    
    simple_cache.delete(key)

def get_cache_stats() -> Dict[str, Any]:
    """Получить статистику кэша"""
    return cache_stats.get_stats()

def reset_cache_stats():
    """Сбросить статистику"""
    cache_stats.reset()

# === RATE LIMITING ===

class RateLimiter:
    def __init__(self, max_requests: int = 100, window: int = 60):
        self.max_requests = max_requests
        self.window = window
    
    def is_allowed(self, key: str) -> bool:
        if redis_client:
            try:
                current = redis_client.get(key)
                if current is None:
                    redis_client.setex(key, self.window, 1)
                    return True
                
                if int(current) >= self.max_requests:
                    return False
                
                redis_client.incr(key)
                return True
            except:
                return True
        
        now = time.time()
        window_key = f"{key}:{int(now // self.window)}"
        
        current = simple_cache.get(window_key)
        if current is None:
            simple_cache.set(window_key, 1, self.window)
            return True
        
        if current >= self.max_requests:
            return False
        
        simple_cache.set(window_key, current + 1, self.window)
        return True

rate_limiter = RateLimiter(max_requests=100, window=60)

def rate_limit(max_requests: int = 100, window: int = 60):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request, jsonify
            
            client_ip = request.remote_addr or 'unknown'
            key = f"rate:{client_ip}:{f.__name__}"
            
            if not rate_limiter.is_allowed(key):
                return jsonify({
                    "error": "Too many requests",
                    "retry_after": window
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def cached(ttl: int = 300, key_prefix: str = ""):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key_args = f"{args}:{kwargs}"
            cache_key = f"{key_prefix}:{f.__name__}:{hash(key_args)}"
            
            cached_result = cache_get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = f(*args, **kwargs)
            cache_set(cache_key, result, ttl)
            
            return result
        return decorated_function
    return decorator

def clear_player_cache(chat_id: str):
    cache_delete(f"player:{chat_id}")

def clear_shop_cache():
    from app.utils.cache import cache_delete
    cache_delete("shop:all")

def clear_all_cache():
    if redis_client:
        try:
            redis_client.flushdb()
        except:
            pass
    simple_cache.clear()
    cache_stats.reset()
