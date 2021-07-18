from google_spreadsheet_writer.gspread_writer_base_class import GspreadWriterBase
from common.utils import pretty_print


class GspreadDeveloperWriter(GspreadWriterBase):
    def _fill_developer_spreadsheet(self, spreadsheet, developer):
        if self._debug:
            pretty_print("Filling data in, creating worksheets:")

        all_history_worksheet = self._add_worksheet_for_all_history(
            spreadsheet)

        for timeframe_and_categories in developer.get_timeframes_and_categories_with_totals():

            totals_per_categories = timeframe_and_categories["totals"]

            categories_issues = timeframe_and_categories["categories_issues"]
            timeframe_str = timeframe_and_categories["timeframe_str"]

            self._add_and_fill_worksheet_for_timeframe(
                spreadsheet, totals_per_categories, categories_issues, timeframe_str)

            self._fill_worksheet_for_all_history(
                all_history_worksheet, totals_per_categories, timeframe_str)

        if self._debug:
            pretty_print("Flushing all rows")
        self._flush_rows()

    def update(self, developer):

        spreadsheet = self._create_or_open_spreadsheet(developer.name)
        if spreadsheet is None:
            return False

        self._cleanup_spreadsheet_and_setup_default_worksheets(
            spreadsheet, is_developer=True)

        developer_totals = self._fill_developer_spreadsheet(
            spreadsheet, developer)

        self._share_permissions(spreadsheet, [developer])

        return True, developer_totals

    def check_developer_for_update_demand(self, developer):
        spreadsheet = self._create_or_open_spreadsheet(developer.name)
        if spreadsheet is None:
            return False

        helper_worksheet = self._safe_worksheet_open(
            spreadsheet, "Helper")
        if helper_worksheet is None:
            return False

        helper_worksheet.update_acell("E1", "Force Update")
        helper_worksheet.update_acell(
            "F2", "Presence of this means that you can force an update, Please set E2 to 1 if you want to update the spreadsheet, some time will pass before update is done")

        if helper_worksheet.acell("E2").value == "1":
            if self._debug:
                pretty_print(
                    "Developer demand an update")
            helper_worksheet.update_acell("E2", 0)
            return True

        return False
