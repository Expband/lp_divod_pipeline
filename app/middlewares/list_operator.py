from typing import TypeVar, Generic, Sequence

T = TypeVar("T")

async def chunk_list(data: list[T], chunk_size: int) -> list[list[T]]:
    """Розділяє список на підсписки заданого розміру."""
    if chunk_size <= 0:
        raise ValueError("chunk_size має бути більшим за 0")

    result: list[list[T]] = []
    for i in range(0, len(data), chunk_size):
        result.append(data[i:i + chunk_size])
    return result