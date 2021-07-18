from jira import JIRA
from string import Template
from common.utils import pretty_print


class JiraConnector:
    def __init__(self, config, credentials, debug):
        try:
            self._jira = JIRA(

                server=config["server"],

                basic_auth=(credentials["login"], credentials["password"])
            )
            self._not_connected = False
        except Exception as e:
            self._not_connected = True
            if self._debug:
                pretty_print("Failed to connect to Jira: " + str(e))

        self._config = config
        self._base_query_template = self._prepare_base_query_template()

        self._debug = debug

    def _prepare_base_query_template(self):
        # query for all not resolved tickets plus resolved with "Done" within timeframe
        # all_tickets_query = Template(
        #     'project in ($projects) AND ((status was not in (Resolved, Rejected) during ($start_date, $end_date)) or (resolutiondate >= $start_date and resolutiondate <= $end_date and resolution = Done)) and assignee = $developer')

        # query for all issues which assignee is given developer
        all_issues_query_template = Template(
            'project in ($projects) and developer = $developer_login')

        return all_issues_query_template

    def is_not_connected(self):
        return self._not_connected

    def query(self, developer):

        query = self._base_query_template.substitute(
            projects=",".join(self._config["projects"]), developer_login=developer.login)

        if self._debug:
            pretty_print(query)

        issues = self._jira.search_issues(
            query,

            # customfield_10006 is Story Points
            # customfield_13405 is Accepted on Demo
            fields="summary,reporter,status,updated,timetracking,worklog,customfield_10006,customfield_13405",

            expand="changelog"
        )

        for issue in issues:

            if self._debug:
                pretty_print(
                    issue.raw['fields'])

            total_time_spent_by_assignee = 0

            # parsing worklog entries and counting time only for given developer
            for worklog in issue.fields.worklog.worklogs:
                if str(worklog.author) == developer.name:
                    total_time_spent_by_assignee += worklog.timeSpentSeconds

            if self._debug:
                pretty_print(issue.key)

            # extracting original estimate
            original_estimate_seconds = None
            if issue.fields.customfield_10006 is not None:
                if self._debug:
                    pretty_print(
                        "Using Story Points for loe calculation")
                # points are in 1/2 working days (1point=4h)
                original_estimate_seconds = float(
                    str(issue.fields.customfield_10006)) * 4 * 3600

            # extracting remaining estimate
            remaining_estimate_seconds = None
            # Code below did work, but it now fails on empty timetracking,
            # it can be connected both to new JIRA Python lib and changes to IOW Jira Server
            # as as of now there is no value in this fields - simply commenting it out
            # if hasattr(issue.fields.timetracking, "remainingEstimateSeconds"):
            #     remaining_estimate_seconds = issue.fields.timetracking.remainingEstimateSeconds

            # evaluating efficieny for given task
            accuracy = None
            if (original_estimate_seconds is not None) and (original_estimate_seconds > 0):
                accuracy = total_time_spent_by_assignee / \
                    (1.0 * original_estimate_seconds)

            # simple presence of the field denotes truth
            accepted_on_demo = issue.fields.customfield_13405 is not None

            # a way to get raw values of all requested fields, great for debug
            # if self._debug:
            #     pretty_print(
            #         issue.raw['fields'])

            # TODO: config for issue info assembling
            issue_info = {
                "key": issue.key,
                "link": "https://jira.iponweb.net/browse/" + issue.key,
                "summary": issue.fields.summary,
                "status": str(issue.fields.status),
                "updated": issue.fields.updated,
                "reporter": str(issue.fields.reporter),
                "histories": issue.changelog.histories,
                "original_estimate_seconds": original_estimate_seconds,
                "remaining_estimate_seconds": remaining_estimate_seconds,
                "total_time_spent_seconds": total_time_spent_by_assignee,
                "accepted_on_demo": accepted_on_demo,
                "accuracy": accuracy,
            }

            if self._debug:
                pretty_print(issue_info)

            developer.store_issue(issue_info)
