from oauth2client.service_account import ServiceAccountCredentials
from string import Template
from gspread.client import Client as ClientV4

from abc import ABC, abstractmethod
import time
import gspread
from common.utils import pretty_print

# TODO: add graph
# TODO: add coloring for accuracy


class GspreadWriterBase(ABC):
    def __init__(self, team, credentials_path, config, statuses_categories, debug):
        self._team = team
        self._config = config
        self._statuses_categories = statuses_categories
        self._debug = debug
        self._rows_storage_per_worksheet = {}
        self._worksheet_object = {}

        try:
            # use creds to create a client to interact with the Google Drive API
            scope = ['https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                credentials_path, scope)
            self._client = gspread.authorize(creds)
            self._monkey_patch_request(self._client)
            self._not_connected = False

        except Exception as e:
            self._not_connected = True
            if self._debug:
                pretty_print(
                    "Failed to create google client: " + str(e))

        self._spreadsheet_name_template = Template(
            "Agile Monitor - $team: $developer_name")

    def _insert_row(self, worksheet, row):
        if not worksheet.title in self._rows_storage_per_worksheet:
            self._rows_storage_per_worksheet[worksheet.title] = {
                "worksheet_object": worksheet,
                "rows": []
            }

        self._rows_storage_per_worksheet[worksheet.title]["rows"].append(row)

    def _flush_rows(self):
        for worksheet_title, worksheet_storage in self._rows_storage_per_worksheet.items():
            worksheet_storage["worksheet_object"].insert_rows(
                worksheet_storage["rows"])

    def _monkey_patch_request(self, client, retry_delay=10):

        def request(*args, **kwargs):
            try:
                return ClientV4.request(client, *args, **kwargs)
            except gspread.exceptions.APIError as e:
                if str(e).find("Quota exceeded"):
                    print("Google APIError: Quota exceeded, waiting " +
                          str(retry_delay) + "sec...")
                    time.sleep(retry_delay)
                    return request(*args, **kwargs)
                else:
                    raise e

        client.request = request

    def is_not_connected(self):
        return self._not_connected

    def _create_or_open_spreadsheet(self, developer_name=""):
        spreadsheet_name = self._spreadsheet_name_template.substitute(
            team=self._team,
            developer_name=developer_name)

        if self._debug:
            pretty_print(
                "Opening or creating spreadsheet of " + developer_name)

        spreadsheet = None
        try:
            spreadsheet = self._client.open(
                spreadsheet_name)
        except Exception as e:
            if self._debug:
                pretty_print(
                    "Were not able to open spreadsheet, trying to create one: " + str(e))
            try:
                spreadsheet = self._client.create(
                    spreadsheet_name)
            except Exception as e:
                if self._debug:
                    pretty_print(
                        "Were not able to create spreadsheet, terminating: " + str(e))

        return spreadsheet

    def _share_permissions(self, spreadsheet, developers):
        # TODO catch exceptions
        if self._debug:
            pretty_print("Sharing permissions")

        for sharing_description in self._config["sharing"]["share_with_emails"]:
            if self._debug:
                pretty_print(
                    "\tSharing with " + sharing_description["email"])
            spreadsheet.share(
                sharing_description["email"], perm_type=sharing_description["perm_type"], role=sharing_description["role"])

        if self._config["sharing"]["share_with_active_developers"]:
            for developer in developers:
                if not developer.is_active():
                    if self._debug:
                        pretty_print(
                            "\tSkipping sharing permission with inactive " + developer["email"])
                    continue

                if self._debug:
                    pretty_print(
                        "\tSharing permission with " + developer.email)
                spreadsheet.share(developer.email,
                                  perm_type='user', role='writer')

    def _safe_worksheet_open(self, spreadsheet, worksheet_title):
        if self._debug:
            pretty_print(
                "Safely opening worksheet: " + worksheet_title)

        worksheet = None
        try:
            worksheet = spreadsheet.worksheet(worksheet_title)
        except Exception as e:
            if self._debug:
                pretty_print("Failed opening: " + str(e))

        return worksheet

    def _fill_helper_worksheet(self, worksheet):
        index_row = 1
        self._insert_row(worksheet, ["category", "statuses"])
        index_row += 1
        for category, statuses in self._statuses_categories.items():
            concat_statuses = ""
            for status in statuses:
                if concat_statuses != "":
                    concat_statuses += "\n"
                concat_statuses = concat_statuses + status
            self._insert_row(worksheet, [category, concat_statuses])
            index_row += 1

    def _cleanup_spreadsheet_and_setup_default_worksheets(self, spreadsheet, is_developer):
        sheets_to_keep = set(["Helper", "All History"] +
                             self._config["custom_sheets"])

        if self._debug:
            pretty_print(
                "Deleting all present worksheets first, apart from " + str(sheets_to_keep))

        helper_worksheet = self._safe_worksheet_open(spreadsheet, "Helper")
        if helper_worksheet is None:
            helper_worksheet = spreadsheet.add_worksheet(
                title="Helper", rows=1, cols=10)
            self._fill_helper_worksheet(helper_worksheet)
        elif self._config["recreate_helper_worksheet"]:
            helper_worksheet.clear()
            self._fill_helper_worksheet(helper_worksheet)

        for worksheet in spreadsheet.worksheets():
            if not (worksheet.title in sheets_to_keep):
                if self._debug:
                    pretty_print("Deleting: " + worksheet.title)
                spreadsheet.del_worksheet(worksheet)

    def _fill_worksheet_for_timeframe_with_totals_per_category(self, timeframe_worksheet, totals_per_categories):
        self._insert_row(timeframe_worksheet,
                         ["category", "total_issues", "focus_factor", "total_estimated_loe", "total_spent_loe", "average_accuracy"])

        for category, totals in totals_per_categories.items():
            self._insert_row(timeframe_worksheet,
                             [category, totals["total_issues"], totals["focus_factor"], totals["total_estimated_loe"], totals["total_spent_loe"], totals["average_accuracy"]])

        self._insert_row(timeframe_worksheet, [])

    def _fill_worksheet_for_timeframe_with_header_for_category_details(self, timeframe_worksheet):
        # TODO populate all fields automatically & have an autoheader
        self._insert_row(timeframe_worksheet,
                         ["category", "issue_key", "issue_link", "issue_summary", "issue_accuracy", "estimated_loe", "spent_loe"])

    def _fill_worksheet_for_timeframe_with_issue_details_per_category(self, timeframe_worksheet, timeframe_and_categories):
        for category, issues_array in timeframe_and_categories["categories"].items():
            for issue in issues_array:

                # TODO add convert seconds to loe with configurable loe
                accuracy = "None" if issue["accuracy"] is None else issue["accuracy"]
                est_loe = "None" if issue["original_estimate_seconds"] is None else issue["original_estimate_seconds"] / 3600.0 / 4
                spent_loe = "None" if issue["total_time_spent_seconds"] is None else issue[
                    "total_time_spent_seconds"] / 3600.0 / 4

                self._insert_row(timeframe_worksheet,
                                 [category, issue["key"], issue["link"], issue["summary"], accuracy, est_loe, spent_loe])

            if len(issues_array) > 0:
                self._insert_row(timeframe_worksheet,
                                 ["<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<", "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<", "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
                                  "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<", "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<", "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"])

    def _add_and_fill_worksheet_for_timeframe(self, spreadsheet, totals_per_categories, categories_issues, timeframe_str):
        if self._debug:
            pretty_print(
                "Creating worksheet for: " + timeframe_str)

        # TODO - do not add every timeframe for everydev (skip frames w/o info)
        timeframe_worksheet = spreadsheet.add_worksheet(
            title=timeframe_str, rows=1, cols=6)

        self._fill_worksheet_for_timeframe_with_totals_per_category(
            timeframe_worksheet, totals_per_categories)
        self._fill_worksheet_for_timeframe_with_header_for_category_details(
            timeframe_worksheet)
        self._fill_worksheet_for_timeframe_with_issue_details_per_category(
            timeframe_worksheet, categories_issues)

    def _add_worksheet_for_all_history(self, spreadsheet):
        if self._debug:
            pretty_print("Creating worksheet for All History")

        all_history_worksheet = self._safe_worksheet_open(
            spreadsheet, "All History")
        if all_history_worksheet is None:
            all_history_worksheet = spreadsheet.add_worksheet(
                title="All History", rows=1, cols=5)
        else:
            all_history_worksheet.clear()

        self._insert_row(all_history_worksheet, ["timeframe", "category", "total_issues", "focus_factor", "total_estimated_loe",
                                                 "total_spent_loe", "average_accuracy"])

        return all_history_worksheet

    def _fill_worksheet_for_all_history(self, all_history_worksheet, totals_per_categories, timeframe_str):
        if self._debug:
            pretty_print(
                "Filling worksheet for All History for timeframe: " + timeframe_str)

        for category, totals in totals_per_categories.items():
            if not category in self._config["categories_to_aggregate"]:
                continue

            self._insert_row(all_history_worksheet,
                             [timeframe_str, category, totals["total_issues"], totals["focus_factor"], totals["total_estimated_loe"], totals["total_spent_loe"], totals["average_accuracy"]])

    @abstractmethod
    def update(self):
        pass
