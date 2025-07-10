class SmallGroupHandler:
    def __init__(self, group, adults, carriages, train, st_module, group_id, confirmation_callback=None):
        self.group = group
        self.adults = adults
        self.carriages = carriages
        self.train = train
        self.st = st_module
        self.group_id = group_id
        self.confirmation_callback = confirmation_callback

    def assign(self):
        if self.adults < 1:
            return False
        
        group_size = self.group["size"]
        toddlers = self.group.get("toddlers", 0)

        best_carriage = None

        # Priority for groups of 1–2
        priority_order = ["1", "8", "4", "5", "2", "3", "6", "7"]

        for priority_num in priority_order:
            for carriage in self.carriages:
                if (carriage["number"] == priority_num 
                    and not carriage.get("occupied", False) 
                    and group_size <= carriage["capacity"]):
                    best_carriage = carriage
                    break
            if best_carriage:
                break

        # Fallback: smallest suitable carriage
        if not best_carriage:
            for carriage in self.carriages:
                if not carriage.get("occupied", False) and group_size <= carriage["capacity"]:
                    if best_carriage is None or carriage["capacity"] < best_carriage["capacity"]:
                        best_carriage = carriage

        if best_carriage:
            best_carriage["occupied"] = True
            best_carriage["group_size"] = group_size
            best_carriage["toddlers"] = toddlers
            best_carriage["group_id"] = self.group_id
            return True

        return False

