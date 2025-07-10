
def only_c4_c5_available(carriages, group_size):
    c4 = next((c for c in carriages if c["number"] == "4" and not c["occupied"]), None)
    c5 = next((c for c in carriages if c["number"] == "5" and not c["occupied"]), None)
    total_c45_capacity = sum(c["capacity"] for c in [c4, c5] if c)

    if total_c45_capacity < group_size:
        return False

    for c in carriages:
        if c["occupied"]:
            continue
        if c["number"] in ["4", "5"]:
            continue
        if c["capacity"] >= group_size:
            return False

    return True

def only_c1_c8_available(carriages, group_size):
    c1 = next((c for c in carriages if c["number"] == "1" and not c["occupied"]), None)
    c8 = next((c for c in carriages if c["number"] == "8" and not c["occupied"]), None)
    total_c18_capacity = sum(c["capacity"] for c in [c1, c8] if c)

    if total_c18_capacity < group_size:
        return False

    for c in carriages:
        if c["occupied"]:
            continue
        if c["number"] in ["1", "8"]:
            continue
        if c["capacity"] >= group_size:
            return False

    return True
