import argparse


def setup_arguments_parser():
    # TODO: add proper validation of all config fields
    arguments_parser = argparse.ArgumentParser(
        description='Jira querier to create reports for loe hitting')
    arguments_parser.add_argument("--config_path", required=True, dest="config_path",
                                  help="path to general configuration file, see config/config_example.json for details")
    arguments_parser.add_argument("--jira_credentials_path", required=True, dest="jira_credentials_path",
                                  help="path to credentials for logging into jira, see config/jira_credentials_example.json for details")
    arguments_parser.add_argument("--google_credentials_path", required=True, dest="google_credentials_path",
                                  help="path to credentials for logging into jira, see config/google_credentials_example.json for details")
    arguments_parser.add_argument(
        "--on_demand_mode", action='store_true', required=False, dest="on_demand_mode", default=False, help="makes process to enter an infinite loop, it update Helper sheet with Force Update cell for each developer and monitors it periodically")
    arguments_parser.add_argument(
        "--debug", action='store_true', required=False, dest="debug", default=False, help="enables detailed debug output")

    return arguments_parser
