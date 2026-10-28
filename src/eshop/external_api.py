import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)


async def fetch_product_with_retry(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    base_url: str,
    product_id: int,
    max_retries: int = 3,
) -> dict:
    url = f"{base_url.rstrip('/')}/products/{product_id}"
    async with semaphore:
        for attempt in range(1, max_retries + 1):
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                logger.warning(
                    f"Спроба {attempt}/{max_retries} для {url} завершилась помилкою: {exc}"
                )
                if attempt == max_retries:
                    return {
                        "id": product_id,
                        "error": str(exc),
                        "status": "failed",
                    }
                # Експоненційний backoff
                await asyncio.sleep(0.1 * (2 ** (attempt - 1)))

    return {"id": product_id, "error": "Unknown error", "status": "failed"}


async def fetch_multiple_products_async(
    base_url: str,
    product_ids: list[int],
    max_concurrency: int = 3,
    timeout_seconds: float = 5.0,
    client: httpx.AsyncClient | None = None,
) -> list[dict]:
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _run(c: httpx.AsyncClient) -> list[dict]:
        tasks = [
            asyncio.create_task(
                fetch_product_with_retry(
                    client=c,
                    semaphore=semaphore,
                    base_url=base_url,
                    product_id=pid,
                    max_retries=3,
                )
            )
            for pid in product_ids
        ]
        return list(await asyncio.gather(*tasks))

    try:
        if client is not None:
            return await asyncio.wait_for(_run(client), timeout=timeout_seconds)
        else:
            async with httpx.AsyncClient(timeout=timeout_seconds) as new_client:
                return await asyncio.wait_for(_run(new_client), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.error(f"Асинхронний запит перевищив ліміт часу {timeout_seconds}с")
        raise