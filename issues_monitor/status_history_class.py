from common.utils import pretty_print


class StatusHistory:
    def __init__(self, debug):

        self.history_dict = {}
        self.history_array = []
        self.sorted_history = []
        self.requires_resort = False

        self.debug = debug

    def remember_status(self, date, status):

        self.history_dict[date] = status
        self.requires_resort = True

    def _rearrange_statuses_historically_by_date(self):

        if self.requires_resort:
            self.history_array = []

            for date, status in self.history_dict.items():
                self.history_array.append({"date": date, "status": status})

            self.sorted_history = sorted(
                self.history_array, key=lambda i: i['date'])
            self.requires_resort = False

    def get_status_by_date(self, date):

        self._rearrange_statuses_historically_by_date()

        if self.debug:
            pretty_print(
                "Getting status by date for:" + date + " using history:")
            pretty_print(self.sorted_history)

        found_status_and_date = None
        for status_and_date in self.sorted_history:

            # monitor should treat each timeframe mathematically as [start_date, end_date), as start date is usually monday and we do not want to have it overlapped
            if date <= self._convert_jira_date_to_yyyy_mm_dd(status_and_date["date"]):
                break

            found_status_and_date = status_and_date

        if self.debug:
            pretty_print("Found:")
            pretty_print(found_status_and_date)

        return found_status_and_date

    def _convert_jira_date_to_yyyy_mm_dd(self, date):
        # Jira stores date as: 2018-08-27T10:34:14.525+0000 for e.g.
        return date[0:10]

    def get_statuses_set_after_the_date(self, date):

        self._rearrange_statuses_historically_by_date()

        if self.debug:
            pretty_print(
                "Getting statuses after the date: " + date + " using history:")
            pretty_print(self.sorted_history)

        found_status_and_date_array = []
        for status_and_date in self.sorted_history:

            # for the reason of [start_date, end_date) frames, we use <= here.
            if date <= self._convert_jira_date_to_yyyy_mm_dd(status_and_date["date"]):
                found_status_and_date_array.append(status_and_date)

        if self.debug:
            pretty_print("Found further:")
            pretty_print(found_status_and_date_array)

        return found_status_and_date_array

    def is_empty(self):

        self._rearrange_statuses_historically_by_date()

        return len(self.sorted_history) == 0
