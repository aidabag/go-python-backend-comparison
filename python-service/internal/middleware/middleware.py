import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Интеграция слоя промежуточных обработчиков.

logger = logging.getLogger("api")

class LoggingMiddleware(BaseHTTPMiddleware):
    """Интеграция слоя протоколирования HTTP-вызовов."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        endpoint = request.url.path
        
        try:
            # Делегирование запроса основной логике
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            duration = time.time() - start_time
            # Журналирование завершения запроса
            logger.info(f"{request.method} {endpoint} {status_code} {duration:.4f}s")
            
        return response
