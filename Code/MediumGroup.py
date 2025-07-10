from Code.Utils import only_c4_c5_available, only_c1_c8_available

class MediumGroupHandler:
    def __init__(self, **kwargs):
        self.confirmation_callback = kwargs.get("confirmation_callback")
        self.adults = kwargs.get("adults")
        self.group = kwargs.get("group")
        self.carriages = kwargs.get("carriages")
        self.train = kwargs.get("train")
        self.st_module = kwargs.get("st_module")
        self.group_id = kwargs.get("group_id")

    def assign(self):
        if self.adults < 1:
            return False
        group_size = self.group["size"]
        toddlers = self.group.get("toddlers", 0)

        # Try preferred carriages first
        priority_order = ["2", "3", "6", "7"]
        fallback_order = ["1", "8"]

        # Try priority carriages
        for number in priority_order + fallback_order:
            for carriage in self.carriages:
                if carriage["number"] == number and not carriage.get("occupied", False) and group_size <= carriage["capacity"]:
                    return self._assign_to_carriage(carriage)

        # Check if only carriages 4 and 5 are available
        if only_c4_c5_available(self.carriages, group_size):
            for number in ["4", "5"]:
                for carriage in self.carriages:
                    if carriage["number"] == number and not carriage.get("occupied", False) and group_size <= carriage["capacity"]:
                        return self._assign_to_carriage(carriage)

        # Else: consider 4/5 with confirmation, but only if at least 2 adults
        if self.adults >= 2:
            for number in ["4", "5"]:
                for carriage in self.carriages:
                    if carriage["number"] == number and not carriage.get("occupied", False) and group_size <= carriage["capacity"]:
                        if self.confirmation_callback(carriage["number"], self.group_id):
                            return self._assign_to_carriage(carriage)

        # No assignment possible
        return False

    def _assign_to_carriage(self, carriage):
        carriage["occupied"] = True
        carriage["group_size"] = self.group["size"]
        carriage["toddlers"] = self.group.get("toddlers", 0)
        carriage["group_id"] = self.group_id
        return True
