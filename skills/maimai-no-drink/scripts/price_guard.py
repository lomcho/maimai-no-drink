"""Verify the observed price schema. Reject unknown fee discrepancies."""
def verify_price(response):
    if response.get('success') is not True or response.get('code') != 200:
        raise ValueError('Price calculation did not succeed')
    data = response.get('data', {})
    fields = ['productPrice', 'deliveryPrice', 'packingPrice', 'price']
    for key in fields:
        if type(data.get(key)) is not int or data[key] < 0:
            raise ValueError('Missing or invalid amount: ' + key)
    if sum(data[key] for key in fields[:3]) != data['price']:
        raise ValueError('Fee breakdown differs from payable; inspect new fees or discounts')
    return {'payable_fen': data['price'], 'fees_complete': True,
            'food_fen': data['productPrice'], 'delivery_fen': data['deliveryPrice'],
            'packing_fen': data['packingPrice']}
