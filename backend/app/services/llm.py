import json
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException
from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, AuthenticationError, RateLimitError

from app.config import get_settings


async def generate_text(
    *,
    instructions: str,
    payload: dict[str, object],
    client_factory: Callable[..., Any] = AsyncOpenAI,
) -> str:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(503, "OpenAI API 키를 적어야 해요.")

    try:
        client = client_factory(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout,
            max_retries=0,
        )
        response = await client.responses.create(
            model=settings.openai_model,
            instructions=instructions,
            input=json.dumps(payload, ensure_ascii=False),
        )
        result = (response.output_text or "").strip()
        if not result:
            raise ValueError("empty model response")
        return result
    except HTTPException:
        raise
    except APITimeoutError:
        raise HTTPException(504, "OpenAI 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.") from None
    except APIConnectionError:
        raise HTTPException(503, "OpenAI 서버에 연결할 수 없습니다. 백엔드의 외부 네트워크 연결을 확인해 주세요.") from None
    except AuthenticationError:
        raise HTTPException(503, "OpenAI API 키가 유효하지 않습니다.") from None
    except RateLimitError:
        raise HTTPException(429, "OpenAI 사용 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.") from None
    except Exception as exc:
        raise HTTPException(502, "AI 응답을 생성하지 못했습니다.") from exc
