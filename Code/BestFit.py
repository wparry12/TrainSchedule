import streamlit as st

class BestFit:
    @staticmethod
    def bestFit(carriages, group_size):

        # Avoid carriages 4 and 5 for preference scoring
        avoid_set = {"4", "5"}

        # Disallowed carriage numbers when flag is True and group size is 3 or 4
        disallowed_carriages = []
        if st.session_state.get("no_1_4_5_8_for_group") and 3 <= group_size <= 4:
            disallowed_carriages = [1, 4, 5, 8]

        # Filter carriages based on disallowed list
        filtered_carriages = [
            carriage for carriage in carriages
            if int(carriage["number"]) not in disallowed_carriages
        ]

        best_combo = None

        for i in range(len(filtered_carriages)):
            combo = []
            total_capacity = 0
            avoid_count = 0

            for j in range(i, len(filtered_carriages)):
                carriage = filtered_carriages[j]

                if carriage["occupied"]:
                    break  # Stop if carriage is occupied

                total_capacity += carriage["capacity"]
                combo.append(j)

                if carriage["number"] in avoid_set:
                    avoid_count += 1

                if total_capacity >= group_size:
                    if (
                        best_combo is None or
                        len(combo) < len(best_combo["indexes"]) or
                        (len(combo) == len(best_combo["indexes"]) and (
                            avoid_count < best_combo["avoid_count"] or
                            (avoid_count == best_combo["avoid_count"] and total_capacity < best_combo["capacity"])
                        ))
                    ):
                        best_combo = {
                            "indexes": combo.copy(),
                            "capacity": total_capacity,
                            "avoid_count": avoid_count
                        }
                    break  # Valid combo found, move on

        return (
            {"indexes": best_combo["indexes"], "capacity": best_combo["capacity"]}
            if best_combo else None,
            len(best_combo["indexes"]) if best_combo else 0
        )