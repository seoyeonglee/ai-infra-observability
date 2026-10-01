import argparse
import asyncio
import random

import httpx


async def send(client: httpx.AsyncClient, base_url: str, index: int) -> None:
    simulate_error = index % 20 == 0
    delay_ms = random.choice([50, 80, 120, 250, 400, 1200])
    payload = {
        "prompt": f"observability load request {index}",
        "simulate_error": simulate_error,
        "delay_ms": delay_ms,
    }
    try:
        response = await client.post(f"{base_url}/api/v1/inference", json=payload)
        print(index, response.status_code)
    except httpx.HTTPError as exc:
        print(index, "ERROR", exc)


async def run(total: int, concurrency: int, base_url: str) -> None:
    semaphore = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(timeout=10.0) as client:
        async def limited(index: int):
            async with semaphore:
                await send(client, base_url, index)

        await asyncio.gather(*(limited(i) for i in range(total)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    asyncio.run(run(args.requests, args.concurrency, args.base_url))
