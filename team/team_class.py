from common.utils import pretty_print


class Team():
    def __init__(self, name, debug):
        self.name = name
        self._debug = debug
        self._developers = []
        self._timeframes_and_categories_with_totals = []

    def __iter__(self):
        return self._developers.__iter__()

    def append(self, developer):
        self._developers.append(developer)

    def _prepare_dict_for_totals_per_category(self):
        return {
            "total_estimated_loe": 0,
            "total_spent_loe": 0,
            "average_accuracy": 0,
            "total_issues": 0,
            "focus_factor": 0,
        }

    def get_timeframes_and_categories_with_totals(self):
        if self._timeframes_and_categories_with_totals:
            return self._timeframes_and_categories_with_totals

        if self._debug:
            pretty_print("Calculating totals for Team " + self.name)

        all_timeframes_totals = {}
        # first, we iterate over all developers and their total stats and summarize everything
        # into dict by timeframe_str & category
        for developer in self._developers:
            for timeframe_and_categories in developer.get_timeframes_and_categories_with_totals():
                timeframe_str = timeframe_and_categories["timeframe_str"]
                # we include only active within given team developers for totals for given timeframe
                if developer.was_active(timeframe_str):
                    if not timeframe_str in all_timeframes_totals:
                        all_timeframes_totals[timeframe_str] = {}

                    for category in timeframe_and_categories["totals"].keys():
                        if not category in all_timeframes_totals[timeframe_str]:
                            all_timeframes_totals[timeframe_str][category] = \
                                self._prepare_dict_for_totals_per_category()

                        for value in ("total_estimated_loe", "total_spent_loe", "total_issues"):
                            value_total = timeframe_and_categories["totals"][category][value]
                            all_timeframes_totals[timeframe_str][category][value] += value_total

        if self._debug:
            pretty_print("Detected these timeframes:")
            pretty_print(all_timeframes_totals)

        for timeframe_str, categories_totals in all_timeframes_totals.items():
            max_team_points = 0
            for developer in self._developers:
                if developer.was_active(timeframe_str):
                    max_team_points += developer.get_max_points(timeframe_str)

            if self._debug:
                pretty_print("Max team story points = " + str(max_team_points))

            totals = {}
            for category, category_totals in categories_totals.items():
                if category_totals["total_estimated_loe"] > 0:
                    category_totals["average_accuracy"] = category_totals["total_spent_loe"] / \
                        category_totals["total_estimated_loe"]
                    category_totals["focus_factor"] = 0 if max_team_points == 0 else category_totals["total_estimated_loe"] / max_team_points

                totals[category] = category_totals

            self._timeframes_and_categories_with_totals.append(
                {"timeframe_str": timeframe_str, "totals": totals})

        self._timeframes_and_categories_with_totals.sort(
            key=lambda i: i['timeframe_str'])

        if self._debug:
            pretty_print("Team results:")
            pretty_print(self._timeframes_and_categories_with_totals)

        return self._timeframes_and_categories_with_totals
