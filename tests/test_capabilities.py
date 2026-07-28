from llm_studio.capabilities import CapabilityStatus, get_capabilities


def test_capability_registry_has_truthful_statuses():
    caps = {cap.name: cap for cap in get_capabilities()}

    assert caps["chat_non_stream"].status == CapabilityStatus.AVAILABLE
    assert caps["lora_merge"].status == CapabilityStatus.NOT_IMPLEMENTED
    assert caps["flutter_windows"].status == CapabilityStatus.AVAILABLE
    assert caps["flutter_android"].status == CapabilityStatus.NOT_IMPLEMENTED


def test_capabilities_are_serializable():
    data = [cap.to_dict() for cap in get_capabilities()]

    assert all("name" in item and "status" in item for item in data)
    assert all(item["status"] != "available" for item in data if item["name"].endswith("_android"))
