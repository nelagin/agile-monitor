import datetime
from issues_monitor.issues_storage_class import IssuesStorage
from common.utils import pretty_print, datetime_to_date_str, date_str_to_datetime, dates_to_timeframe_str, timeframe_str_to_timeframe, timeframe_str_to_datetime


class Developer:
    def __init__(self, developer_config, issues_monitor_config, debug):
        for attr_name in ("name", "login", "email", "max_points", "exclude_from_focus"):
            setattr(self, attr_name, developer_config[attr_name])

        self._debug = debug
        self._totals_for_team = {}

        self._issues_storage = IssuesStorage(
            config=issues_monitor_config,
            debug=debug)
        self._timeframes_and_categories_with_totals = []

        self._active_timeframes = []
        for timeframe_str in developer_config["active"]:
            timeframe = timeframe_str_to_timeframe(timeframe_str)
            self._active_timeframes.append(timeframe)

        self._vacation_days = set()
        for timeframe_str in developer_config["vacations"]:
            start_date_obj, end_date_obj = timeframe_str_to_datetime(
                timeframe_str)
            timedelta = datetime.timedelta(days=1)
            while start_date_obj <= end_date_obj:
                self._vacation_days.add(datetime_to_date_str(start_date_obj))
                start_date_obj += timedelta

        if self._debug:
            pretty_print("Initiated Developer: " + self.name)
            pretty_print("Vacations: ")
            pretty_print(self._vacation_days)
            pretty_print("Active:")
            pretty_print(self._active_timeframes)

    def _was_active_in_timeframe(self, timeframe):
        for active_timeframe in self._active_timeframes:
            if timeframe[0] >= active_timeframe[0] and timeframe[1] <= active_timeframe[1]:
                return True
        return False

    def _was_on_vacation_in_timeframe(self, timeframe):
        for vacations_timeframes in self.vacations_timeframes:
            if timeframe[0] >= active_timeframe[0] and timeframe[1] <= active_timeframe[1]:
                return True
        return False

    def get_max_points(self, timeframe_str):
        # max_points for given person is then calculated as (work_days - vacation_days)/work_days * max_points.
        start_date_obj, end_date_obj = timeframe_str_to_datetime(timeframe_str)
        timedelta = datetime.timedelta(days=1)

        if self._debug:
            pretty_print("Getting max points for " +
                         self.name + " for " + timeframe_str)

        work_days = 0
        vacation_days = 0
        while start_date_obj < end_date_obj:
            # 0 is Monday
            if start_date_obj.weekday() < 5:
                date = datetime_to_date_str(start_date_obj)
                if date in self._vacation_days:
                    if self._debug:
                        pretty_print("Day " + date + " is a vacation")
                    vacation_days += 1
                work_days += 1
                if self._debug:
                    pretty_print("Day " + date + " is a work day")

            start_date_obj += timedelta

        max_points = self.max_points * (work_days - vacation_days) / work_days
        if self._debug:
            pretty_print("Max points for " + timeframe_str +
                         ": " + str(max_points))

        return max_points

    def is_active(self):
        # if now() fits into one of developer active timeframes
        now_dt = datetime_to_date_str(datetime.now())

        if self._debug:
            pretty_print("Validating if " + self.name +
                         "is active now: " + now_dt)

        active = self._was_active_in_timeframe(self, [now_dt, now_dt])

        if self._debug:
            pretty_print("Result is " + str(active))

        return active

    def was_active(self, timeframe_str):
        if self.exclude_from_focus:
            if self._debug:
                pretty_print("Developer " + self.name +
                             " is excluded from focus")
            return False

        # developer is considered as active if timefrime fits wholly in one of his active frames
        # spreadsheets with results are shared only with given team active developers
        # for given timeframe, only active members results are counted towards focus factor

        if self._debug:
            pretty_print("Validating if " + self.name +
                         " was active in " + timeframe_str)

        timeframe = timeframe_str_to_timeframe(timeframe_str)
        active = self._was_active_in_timeframe(timeframe)

        if self._debug:
            pretty_print("Result is " + str(active))

        return active

    def _gather_totals_per_categories_for_timeframe(self, timeframe_str, timeframe_and_categories):
        max_points = self.get_max_points(timeframe_str)
        totals_per_categories = {}

        for category, issues_array in timeframe_and_categories["categories"].items():
            if not category in totals_per_categories:
                totals_per_categories[category] = self._prepare_dict_for_totals_per_category(
                )

            category_totals = totals_per_categories[category]

            for issue in issues_array:
                category_totals["total_estimated_loe"] += 0 if issue["original_estimate_seconds"] is None else issue["original_estimate_seconds"] / 3600.0 / 4
                category_totals["total_spent_loe"] += 0 if issue["total_time_spent_seconds"] is None else issue["total_time_spent_seconds"] / 3600.0 / 4
                category_totals["total_issues"] += 1

            if category_totals["total_estimated_loe"] > 0:
                category_totals["average_accuracy"] = category_totals["total_spent_loe"] / \
                    category_totals["total_estimated_loe"]
                category_totals["focus_factor"] = None if max_points == 0 else category_totals["total_estimated_loe"] / max_points

        if self._debug:
            pretty_print(
                "Gathered totals for " + timeframe_str)
            pretty_print(totals_per_categories)

        return totals_per_categories

    def _prepare_dict_for_totals_per_category(self):
        return {
            "total_estimated_loe": 0,
            "total_spent_loe": 0,
            "average_accuracy": 0,
            "total_issues": 0,
            "focus_factor": 0,
        }

    def store_issue(self, issue):
        self._issues_storage.store(issue)

    def get_timeframes_and_categories_with_totals(self):
        if self._timeframes_and_categories_with_totals:
            return self._timeframes_and_categories_with_totals

        issues_array_by_timeframe_and_category = self._issues_storage.get_issues_array_by_timeframe_and_category()

        # all timeframes should be unique - but verifying it for consistency
        duplicate_timeframe_tracker = set()

        # we are reversing it so that latest data is closest to the begging (as usually one wants to know recent data)
        for timeframe_and_categories in reversed(issues_array_by_timeframe_and_category):

            timeframe_str = dates_to_timeframe_str(
                timeframe_and_categories["start_date_str"], timeframe_and_categories["end_date_str"])

            totals_per_categories = self._gather_totals_per_categories_for_timeframe(
                timeframe_str, timeframe_and_categories)

            self._timeframes_and_categories_with_totals.append(
                {
                    "totals": totals_per_categories,
                    "categories_issues": timeframe_and_categories,
                    "timeframe_str": timeframe_str,
                }
            )

            if timeframe_str in duplicate_timeframe_tracker:
                raise RuntimeError(
                    "Encountered duplicated timeframe_str for developer " + self.name)
            else:
                duplicate_timeframe_tracker.add(timeframe_str)

        return self._timeframes_and_categories_with_totals
