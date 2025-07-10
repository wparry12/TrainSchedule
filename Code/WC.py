class WC:
    @staticmethod
    def wheelchair(wheelchair_count, group_size, adults, toddlers, schedule, st, group_id):
        if wheelchair_count == 0 or adults < wheelchair_count:
            return False

        best_option = None  # (waste, train_index, [carriage_numbers])

        for train_index, train in enumerate(schedule):
            if train.get("cancelled", False) or train.get("party_train", False):
                continue

            carriages = sorted(train["carriages"], key=lambda x: int(x["number"]))
            available_carriages = [
                c for c in carriages if not c.get("occupied", False)
            ]

            # Filter for at least enough unoccupied carriage 2s (wheelchair accessible)
            available_c2s = [c for c in available_carriages if c["number"] == "2"]
            if len(available_c2s) < wheelchair_count:
                continue

            carriage_map = {int(c["number"]): c for c in available_carriages}
            max_carriage_num = max(carriage_map.keys(), default=0)

            for start in range(1, max_carriage_num + 1):
                current_group = []
                total_capacity = 0
                wc_in_group = 0
                carriage_nums_used = []

                for num in range(start, max_carriage_num + 1):
                    if num not in carriage_map:
                        break  # Must be consecutive

                    carr = carriage_map[num]
                    capacity = carr["capacity"]
                    if carr["number"] == "2":
                        wc_in_group += 1
                        capacity = 3  # wheelchair reduces usable capacity

                    total_capacity += capacity
                    current_group.append(carr)
                    carriage_nums_used.append(num)

                    if total_capacity >= group_size and wc_in_group >= wheelchair_count:
                        waste = total_capacity - group_size
                        candidate = (waste, train_index, carriage_nums_used)
                        if best_option is None or candidate < best_option:
                            best_option = candidate
                        break

        if not best_option:
            return False

        # Proceed with assignment
        _, selected_train_index, carriage_nums = best_option

        # --- NEW CHECK ---
        if adults < len(carriage_nums):
            return False

        train = schedule[selected_train_index]
        remaining_group = group_size
        remaining_adults = adults
        remaining_toddlers = toddlers
        wc_needed = wheelchair_count

        # Assign carriages
        for num in carriage_nums:
            carriage = next(c for c in train["carriages"] if int(c["number"]) == num)

            is_wc = carriage["number"] == "2" and wc_needed > 0
            max_capacity = 3 if is_wc else carriage["capacity"]
            assign = min(remaining_group, max_capacity)

            toddlers_in_carriage = min(assign, remaining_toddlers // len(carriage_nums))
            carriage.update({
                "occupied": True,
                "group_id": group_id,
                "group_size": assign,
                "toddlers": toddlers_in_carriage,
                "wheelchair": is_wc
            })

            remaining_group -= assign
            remaining_toddlers -= toddlers_in_carriage

            if is_wc:
                wc_needed -= 1
                remaining_adults -= 1  # One adult per wheelchair

        return True

    @staticmethod
    def can_fit_wheelchair(train, group_size, adults, toddlers, wheelchair_count):
        # Simplified version: only check if unoccupied space meets requirements
        carriages = train["carriages"]
        available_capacity = sum(c["capacity"] for c in carriages if not c.get("occupied", False))
        return group_size <= available_capacity and wheelchair_count <= 1
