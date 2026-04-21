from typing import Dict, Any, Optional
from starlette.responses import JSONResponse

# Формирование унифицированных ответов для HTTP-обработчиков.

def write_error(status_code: int, code: str, message: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """Генерация стандартного ответа об ошибке с кодом и описанием."""
    payload = {
        "error": code,
        "message": message
    }
    if details:
        payload["details"] = details
        
    return JSONResponse(payload, status_code=status_code)
