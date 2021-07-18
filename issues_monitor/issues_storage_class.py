import datetime
from issues_monitor.status_history_class import StatusHistory
from issues_monitor.category_determinator_class import CategoryDeterminator
from common.utils import pretty_print, datetime_to_date_str


class IssuesStorage:
    def __init__(self, config, debug):
        self._config = config
        self._debug = debug
        self._issues_dict_by_key = {}

        self._today_date_object = datetime.date.today()

        self._issues_array_by_timeframe_and_category = self._prepare_array_by_timeframe_and_category()

        self._category_determinator = CategoryDeterminator(
            today_date_str=datetime_to_date_str(
                self._today_date_object),
            categories_priority=self._config["categories_priority"],
            statuses_categories=self._config["statuses_categories"],
            continuous_status_categories=self._config["continuous_status_categories"],
            debug=debug,
        )

    def store(self, issue):

        issue_status_history = StatusHistory(
            debug=self._debug)
        issue_demo_history = StatusHistory(
            debug=self._debug)

        for history in issue["histories"]:
            for item in history.items:
                # if self._debug:
                #     pretty_print(
                #         "History item: " + item.field + " " + history.created + item.toString)

                if item.field == 'status':
                    issue_status_history.remember_status(
                        date=history.created, status=item.toString.lower())
                elif item.field == "Accepted on Demo" and issue["accepted_on_demo"] == True:
                    # remembering accepted on demo date only if actual accepted on demo value is True
                    issue_demo_history.remember_status(
                        date=history.created, status="accepted_on_demo")

        # in case changelog history is empty, current status is the one with which issue was created (or migrated)
        if issue_status_history.is_empty():
            issue_status_history.remember_status(
                date=issue["updated"],
                status=issue["status"].lower())

        issue["status_history"] = issue_status_history
        issue["demo_history"] = issue_demo_history
        issue["histories"] = None  # cleaning field since not needed

        self._issues_dict_by_key[issue["key"]] = issue
        # TODO: use memory and do not process already processed timeframes
        self._store_in_categories_and_timeframes(issue)

    def get_issues_array_by_timeframe_and_category(self):
        return self._issues_array_by_timeframe_and_category

    def _prepare_array_by_timeframe_and_category(self):
        statuses_categories = self._config["statuses_categories"]

        monitor_start_date = self._config["monitor_start_date"]
        start_date_object = datetime.date(
            monitor_start_date["year"], monitor_start_date["month"], monitor_start_date["day"])
        today_date_object = self._today_date_object

        if start_date_object >= today_date_object:
            raise ValueError('start date is in the future or is today')

        tick_timedelta = datetime.timedelta(
            days=self._config["monitor_tick_days"])

        current_start_date_object = start_date_object
        current_end_date_object = start_date_object + tick_timedelta

        issues_array_by_timeframe_and_category = []
        while True:
            start_date_str = datetime_to_date_str(
                current_start_date_object)
            end_date_str = datetime_to_date_str(
                current_end_date_object)

            categories = {}
            for issue_category in self._config["statuses_categories"]:
                categories[issue_category] = []

            issues_array_by_timeframe_and_category.append({
                "start_date_str": start_date_str,
                "end_date_str": end_date_str,
                "categories": categories,
            })

            if current_end_date_object > today_date_object:
                break

            current_start_date_object = current_end_date_object
            current_end_date_object = current_end_date_object + tick_timedelta

        return issues_array_by_timeframe_and_category

    def _store_in_categories_and_timeframes(self, issue):

        for timeframe_and_categories in self._issues_array_by_timeframe_and_category:
            if self._debug:
                pretty_print("Storing issue:" + issue["key"] + " for timeframe:" +
                             timeframe_and_categories["start_date_str"] + " - " + timeframe_and_categories["end_date_str"])

            if self._debug:
                pretty_print(
                    "Obtaining categories by timeframe for statuses")

            status_issue_categories = self._category_determinator.get_categories_by_timeframe(
                start_date_str=timeframe_and_categories["start_date_str"],
                end_date_str=timeframe_and_categories["end_date_str"],
                status_history=issue["status_history"],
            )

            if self._debug:
                pretty_print(
                    "Obtaining categories by timeframe for demo")

            demo_issue_categories = self._category_determinator.get_categories_by_timeframe(
                start_date_str=timeframe_and_categories["start_date_str"],
                end_date_str=timeframe_and_categories["end_date_str"],
                status_history=issue["demo_history"],
            )

            issue_categories = status_issue_categories + demo_issue_categories

            if self._debug:
                pretty_print("Storing into futher categories:")
                pretty_print(issue_categories)

            for issue_category in issue_categories:
                timeframe_and_categories["categories"][issue_category].append(
                    issue)
