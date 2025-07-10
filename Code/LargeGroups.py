from Code.BestFit import BestFit

class LargeGroupHandler:
    def __init__(self, group, adults, carriages, train, st_module, group_id, confirmation_callback=None):
        self.group = group
        self.adults = adults
        self.carriages = carriages
        self.train = train
        self.st = st_module
        self.group_id = group_id
        self.confirmation_callback = confirmation_callback

    def assign(self):
        group_size = self.group["size"]
        adults = self.adults
        toddlers = self.group.get("toddlers", 0)

        best_fit_result, carriage_count = BestFit.bestFit(self.carriages, group_size)

        if not best_fit_result:
            return False  # No suitable set of carriages found

        # Check adults vs carriages needed
        if adults < carriage_count:
            return False

        indexes = best_fit_result["indexes"]
        remaining = group_size

        for i in indexes:
            carriage = self.carriages[i]
            to_assign = min(remaining, carriage["capacity"])

            carriage["occupied"] = True
            carriage["group_size"] = to_assign
            carriage["toddlers"] = toddlers if remaining == group_size else 0  # Toddlers only on first carriage
            carriage["group_id"] = self.group_id

            remaining -= to_assign
            if remaining <= 0:
                break

        return True
