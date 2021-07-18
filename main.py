import time
from common.utils import pretty_print, read_config
from common.cli_arguments import setup_arguments_parser
from jira_querier import JiraConnector
from google_spreadsheet_writer import GspreadDeveloperWriter, GspreadTeamWriter
from team import Developer, Team

arguments_parser = setup_arguments_parser()
parsed_arguments = arguments_parser.parse_args()

on_demand_mode = parsed_arguments.on_demand_mode
debug = parsed_arguments.debug

config = read_config(parsed_arguments.config_path)
jira_credentials = read_config(
    parsed_arguments.jira_credentials_path)
google_credentials_path = parsed_arguments.google_credentials_path

while(True):
    if on_demand_mode:
        if debug:
            pretty_print(("Started in on-demand mode.."))

    if debug:
        pretty_print("Authorizing in jira")

    jira_connector = JiraConnector(
        config=config["jira_connector"], credentials=jira_credentials, debug=debug)

    if jira_connector.is_not_connected():
        if debug:
            pretty_print("Jira authorization failed, terminating")
        quit(1)

    if debug:
        pretty_print("Authorizing in google")

    developers_totals = []

    team = Team(
        name=config["team"],
        debug=debug
    )

    for developer in config["developers"]:
        team.append(Developer(
            developer_config=developer,
            issues_monitor_config=config["issues_monitor"],
            debug=debug
        )
        )
    # Start to process all developers

    for developer in team:
        # reconnecting each time due to possible timeout due to long work
        # TODO: writer should be able to re-connect
        gspread_developer_writer = GspreadDeveloperWriter(
            credentials_path=google_credentials_path, team=team.name,
            config=config["google_spreadsheet_writer"], statuses_categories=config["issues_monitor"]["statuses_categories"], debug=debug
        )

        if gspread_developer_writer.is_not_connected():
            if debug:
                pretty_print(
                    "Google authorization failed, terminating")
            quit(1)

        if on_demand_mode:
            if debug:
                pretty_print(
                    "Update is in on demand mode")

            does_require_update = gspread_developer_writer.check_developer_for_update_demand(
                developer=developer,
            )

            if not does_require_update:
                if debug:
                    pretty_print(
                        "Developer " + developer.name + " does not need an update")

                continue

        if debug:
            pretty_print(
                "Creating issues storage for " + developer.name)

        if debug:
            pretty_print("Obtaining data from jira")

        jira_connector.query(
            developer=developer
        )

        if debug:
            pretty_print("Result for " + developer.name + ":")
            pretty_print(
                developer.get_timeframes_and_categories_with_totals())

        if debug:
            pretty_print(
                "Writing to developer " + developer.name + " googlesheet")

        was_updated = gspread_developer_writer.update(
            developer=developer)

        if debug:
            pretty_print(
                "Developer spreasheet was " + ("" if was_updated else "not") + " updated!")

    # Finished processing all developers

    if on_demand_mode:
        if debug:
            pretty_print(("On demand mode iteration finished, waiting.."))
        time.sleep(10)
        # staying in loop until system interruption
    else:
        if debug:
            pretty_print("Now update team spreadsheet with totals")

        gspread_team_writer = GspreadTeamWriter(
            credentials_path=google_credentials_path, team=team.name, config=config[
                "google_spreadsheet_writer"], statuses_categories=config["issues_monitor"]["statuses_categories"], debug=debug
        )

        if gspread_team_writer.is_not_connected():
            if debug:
                pretty_print(
                    "Google authorization failed, terminating")
            quit(1)

        was_updated = gspread_team_writer.update(team)

        if debug:
            pretty_print(
                "Team spreasheet was " + ("" if was_updated else "not") + " updated!")
        # exiting the loop explicitly
        break

if debug:
    pretty_print("All done! Bye!")

exit(0)
