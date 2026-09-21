"""A small syntax fixture, not evidence of deployed runtime behavior."""


def checkout(amount):
    return route_payment(amount)


def route_payment(amount):
    return {"amount": amount, "accepted": True}


def refund(amount):
    return None


def refund_eu(amount):
    return {"amount": amount, "region": "EU"}


def refund_us(amount):
    return {"amount": amount, "region": "US"}
