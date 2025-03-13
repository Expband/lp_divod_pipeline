import asyncio

from app.middlewares.dilovod_client.dilovod_query_builder import DilovodQueryBuilder

dqb = DilovodQueryBuilder()

dilovod_shipment_id = '1106800000006486'
dilovod_response_object = {
    "header": {
        "id": {
            "id": "1109100000042916",
            "pr": "12.03.2025 Замовлення НР00041895"
        },
        "date": "2025-03-12 19:41:40",
        "number": "НР00041895",
        "presentation": {
            "ru": "12.03.2025 Заказ НР00041895",
            "uk": "12.03.2025 Замовлення НР00041895"
        },
        "delMark": "0",
        "posted": "1",
        "remark": "Заказ из CRM: 17418012994, warmGear",
        "baseDoc": {
            "id": "0",
            "pr": None
        },
        "version": "2",
        "firm": {
            "id": "1100400000001001",
            "pr": "Здохлій Данило Олександрович"
        },
        "business": {
            "id": "1115000000000001",
            "pr": "[access restricted]"
        },
        "storage": {
            "id": "1100700000000001",
            "pr": None
        },
        "person": {
            "id": "1100100000043657",
            "pr": "Лилия Майборода"
        },
        "manager": {
            "id": "0",
            "pr": "[access restricted]"
        },
        "department": {
            "id": "1101900000000001",
            "pr": "Основний підрозділ"
        },
        "contract": {
            "id": "0",
            "pr": "[access restricted]"
        },
        "contact": {
            "id": "0",
            "pr": "[access restricted]"
        },
        "currency": {
            "id": "1101200000001001",
            "pr": "грн."
        },
        "amountCur": "680.00",
        "rate": "1.0000",
        "paymentForm": {
            "id": "1110300000001001",
            "pr": "[access restricted]"
        },
        "author": {
            "id": "0",
            "pr": "[access restricted]"
        },
        "deliveryRemark_forDel": "20451121647528",
        "priceType": {
            "id": "1101300000001001",
            "pr": "[access restricted]"
        },
        "mrkupPercent_forDel": "0.000",
        "discountPercent": "0.000",
        "state": {
            "id": "1111500000000005",
            "pr": "[access restricted]"
        },
        "deliveryPoint": {
            "id": "0",
            "pr": "[access restricted]"
        },
        "weight": "0.000",
        "allowAnyStorage_forDel": "0",
        "supplyDate": "0000-00-00 00:00:00",
        "reserveDate": "0000-00-00 00:00:00",
        "payment_forDel": "0.00",
        "cashAccount": {
            "id": "0",
            "pr": None
        },
        "cashItem_forDel": {
            "id": "0",
            "pr": None
        },
        "payBefore": "0000-00-00 00:00:00",
        "placed": "0",
        "taxAccount": "0",
        "tradeChanel": {
            "id": "0",
            "pr": "[access restricted]"
        },
        "userPresentation": "0",
        "discountCard": {
            "id": "0",
            "pr": "[access restricted]"
        },
        "details": "",
        "settlementsKind": {
            "id": "1103300000000001",
            "pr": "Розрахунки з покупцями"
        },
        "remarkForPerson": "",
        "remarkFromPerson": "",
        "deliveryMethod_forDel": {
            "id": "1110400000001001",
            "pr": "Нова пошта"
        },
        "trackNum_forDel": "",
        "taxManual": "0",
        "taxIncluded": "0",
        "cancelReason": {
            "id": "0",
            "pr": "[access restricted]"
        }
    },
    "tableParts": {
        "tpGoods": {
            "105376": {
                "rowNum": "1",
                "good": "1100300000031128",
                "good__pr": "ОДЯГ Versace Man Eau Fraiche 100ml",
                "price": "680.00000",
                "qty": "1.000",
                "baseQty": "1.000",
                "priceAmount": "680.00",
                "unit": "1103600000000001",
                "unit__pr": "[access restricted]",
                "mrkup_forDel": "0.00",
                "discount": "0.00",
                "amountCur": "680.00",
                "discountPercent": "0.0",
                "mrkupPercent_forDel": "0.0",
                "ratio": "0.0000",
                "weight": "0.000",
                "gType_forDel": "0",
                "gType_forDel__pr": None,
                "gCharForDelete": "0",
                "gCharForDelete__pr": "[access restricted]",
                "qtyReserve": "0.000",
                "qtyPurchase": "0.000",
                "qtyProd": "0.000",
                "supplier": "0",
                "supplier__pr": None,
                "supplierPrice": "0.00000",
                "supplierCurrency": "0",
                "supplierCurrency__pr": None,
                "storage": "0",
                "storage__pr": None,
                "remark": "",
                "promotion": "0",
                "promotion__pr": "[access restricted]",
                "accGood": "1119000000001016",
                "accGood__pr": "Товари",
                "hash": "",
                "comPrice": "0.00000",
                "comAmount": "0.00",
                "vatTax": "0",
                "vatTax__pr": None,
                "vatAmount": "0.00",
                "salesTaxes": "0",
                "salesTaxes__pr": "[access restricted]",
                "sltTax1": "0",
                "sltTax1__pr": None,
                "sltRate1": "0.00",
                "sltBase1": "0.00",
                "sltAmount1": "0.00",
                "sltTax2": "0",
                "sltTax2__pr": None,
                "sltRate2": "0.00",
                "sltBase2": "0.00",
                "sltAmount2": "0.00",
                "printName": "",
                "id": "105376"
            }
        }
    },
    "misc": False
}

request_body = asyncio.run(dqb.get_data_to_cashIn(
    dilovod_object=dilovod_response_object,
    shipment_id=dilovod_shipment_id
))
print(request_body)
