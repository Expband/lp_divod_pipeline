from collections import defaultdict


class DilovodOperator:
    async def sort_orders_by_delivery(
            self,
            dilovod_orders: list[dict]) -> None:
        sorted_orders = defaultdict(list)
        for order in dilovod_orders:
            delivery_method: str = (
                order['header']['deliveryMethod_forDel']['id'])
            sorted_orders[delivery_method].append(order)
        return dict(sorted_orders)

    async def get_id_from_list_order(self, orders: list[dict]) -> list[str]:
        processed_orders_id: list[str] = []
        for order in orders:
            order_id: str = order['header']['id']['id']
            processed_orders_id.append(order_id)
        return processed_orders_id
