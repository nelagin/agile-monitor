from google_spreadsheet_writer.gspread_writer_base_class import GspreadWriterBase
from common.utils import pretty_print


class GspreadTeamWriter(GspreadWriterBase):
    def _fill_team_spreadsheet(self, spreadsheet, team):
        if self._debug:
            pretty_print("Filling data in, creating worksheets:")

        all_history_worksheet = self._add_worksheet_for_all_history(
            spreadsheet)

        for timeframe_and_categories_with_totals in team.get_timeframes_and_categories_with_totals():
            self._fill_worksheet_for_all_history(
                all_history_worksheet, timeframe_and_categories_with_totals["totals"], timeframe_and_categories_with_totals["timeframe_str"])

        if self._debug:
            pretty_print("Flushing all rows")
        self._flush_rows()

    def update(self, team):

        spreadsheet = self._create_or_open_spreadsheet()
        if spreadsheet is None:
            return False

        self._share_permissions(spreadsheet, team)

        self._cleanup_spreadsheet_and_setup_default_worksheets(
            spreadsheet, is_developer=False)

        self._fill_team_spreadsheet(
            spreadsheet, team)

        return True
