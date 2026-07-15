from model.order_status import OrderStatus


def test_order_status_has_five_members_with_matching_string_values():
    assert OrderStatus.RESERVED.value == "RESERVED"
    assert OrderStatus.REJECTED.value == "REJECTED"
    assert OrderStatus.PRODUCING.value == "PRODUCING"
    assert OrderStatus.CONFIRMED.value == "CONFIRMED"
    assert OrderStatus.RELEASE.value == "RELEASE"
    assert len(OrderStatus) == 5
