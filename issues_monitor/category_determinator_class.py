from common.utils import pretty_print


class CategoryDeterminator:
    def __init__(self, today_date_str, categories_priority, statuses_categories, continuous_status_categories, debug):

        self.today_date_str = today_date_str
        self.status_to_category_mapping = self._prepare_status_to_category_mapping(
            statuses_categories)
        self.continuous_status_categories = continuous_status_categories
        self.categories_priority = categories_priority

        self.debug = debug

    # TODO: add validation that categories have no intersecting statuses
    def _prepare_status_to_category_mapping(self, statuses_categories):
        status_to_category_mapping = {}
        for issue_category in statuses_categories:
            for issue_category_status in statuses_categories[issue_category]:
                if issue_category_status in status_to_category_mapping:
                    status_to_category_mapping[issue_category_status].append(
                        issue_category)
                else:
                    status_to_category_mapping[issue_category_status] = [
                        issue_category]

        return status_to_category_mapping

    # FIXME: initially same status can make it into different categories, but decided to abandon it since it easies analyzing and brings little value
    def get_categories_by_timeframe(self, start_date_str, end_date_str, status_history):
        result_categories = []

        found_status_and_date = status_history.get_status_by_date(end_date_str)

        if self.debug:
            pretty_print(
                "For date:" + end_date_str + " found further:")
            pretty_print(found_status_and_date)

        if found_status_and_date is not None:

            # FIXME this ugly conditions & array interation - not needed
            intermediate_categories = self.status_to_category_mapping[
                found_status_and_date["status"]]
            if self.debug:
                pretty_print("Intermediate categories:")
                pretty_print(intermediate_categories)

            for intermediate_category in intermediate_categories:
                if intermediate_category in self.continuous_status_categories:
                    if self.debug:
                        pretty_print(
                            "continuous category - using it as a result")
                    # this is a continuous states, like wip, todo, etc - "resolved/done" issues should not be counted into timeframes where they were not changed to it
                    result_categories.append(intermediate_category)
                else:
                    # this is a deployed/prepared category. need to check:
                    # 1. if it was set before start of timeframe:
                    if found_status_and_date["date"] < start_date_str:
                        if self.debug:
                            pretty_print(
                                "category was reached before start of timeframe, not counting it")
                        return result_categories

                    # 2. if in the future it was changed to category of lower or equal priority
                    intermediate_category_priority = self.categories_priority[intermediate_category]

                    found_status_and_date_array = status_history.get_statuses_set_after_the_date(
                        end_date_str)
                    for future_found_status_and_date in found_status_and_date_array:
                        future_category = self.status_to_category_mapping[
                            future_found_status_and_date["status"]][0]
                        future_category_priority = self.categories_priority[future_category]

                        if self.debug:
                            pretty_print(
                                "Found further future status: ")
                            pretty_print(
                                future_found_status_and_date)

                        if future_category_priority <= intermediate_category_priority:
                            if self.debug:
                                pretty_print("In the future issue was changed to category: " + future_category + " with lower or equal prio of " + str(
                                    future_category_priority) + " than initial prio: " + str(intermediate_category_priority))
                                pretty_print(
                                    "So discrading category")
                            return result_categories

                    result_categories.append(intermediate_category)

        return result_categories
