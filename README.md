# Agile Monitor

## tl;dr usage

docker-compose v.1.26

docker v.19

First, configure:
```
./config/config.json -> setup accordingly to your team & process
./config/jira_credentials.json -> input your login
./config/google_credentials.json -> use bot service account json, obtainable from GCE console
```

From the repository folder, execute:

```
docker-compose build
docker-compose up
```

For more information on changing the way you execute the script, please refer to the comments in Dockerfile

## Intro

Project is dedicated for automating focus factor, loe, accuracy and other useful stats aggregation.

It is designed to be used in two mode:

1) First, when lead launches it with according to his team config setup
2) Second, when lead can setup locally (or e.g. in K8S) script in a mode that allows to trigger individual developers sheet updates (on_demand_mode)

## Overview

### Main

main.py is a launcher for the application. It is logic for usual mode is as follows:

1. Read cli arguments & json configs

2. Create JiraConnector, connect to Jira & authorize

3. Create Team object - to store all developers

4. Create Developer objects with developer info baked in (like vacations, active timeframes, story points, issues) and store them in the Team. Within Developer IssuesStorage object is created with all the definitions about how statuses map into categories.

5. Iterate over Developers in the Team and:

    5.1 Create GspreadDeveloperWriter, connect to Google Sheets API & authorize

    5.2 Pass Developer object to JiraConnector for quering Jira and serializing issues data into internal format, JiraConnector stores them into IssuesStorage via Developer

    5.3 Pass Developer to GspreadDeveloperWriter for serializing developer issues data into dedicated spreadsheet.

6. Create another GspreadTeamWriter connector, pass Team to it &  serialize team aggregated data into dedicated spreadsheet

### Common

Package that contains auxilarry module utils.py that is responsible for debug pretty printing and various time format conversions.

Also contains cli_arguments module that describes & setups command line arguments of the application

### Config

Folder dedicated for config examples and their description

### Team

Package dedicated for encapsulating all data relate to the Team & Developer

#### Team class

Class stores Developers, provides access to them and additionally is responsible for producing total aggregated category stats per the whole team, including focus factor, accuracy, etc.

#### Developer class
Class encapsulates attributes like name, login, vacations, active timeframes, story points, etc.
It also methods that are responsible for providing a result on when developer was active, on vacation, etc, relative to dates.
It also carries knowledge about all developer jira issues, after jira was queried. Additionally class provides methods for aggregating issues statits like spent time, estimations into aggregated format per categories & timeframes

### Jira querier

Package dedicated for encapsulating all interactions with Jira and serializing Jira issues into an internal format and passing them to the Developer

### Issue Monitor

Most complex-logic package that encapsulates sorting of all given Developer issues per configurated timeframes and status-to-category relations. It useses number of euristics that are somewhat documented by comments in the code.
Exactly this package is responsible for relating issues into (timeframe x category), defining when issue was really resolved, accepted on demo/etc.

To elaborate it works as a snapshot of state of things per a moment, for instance if we have a timeframe from monday to friday, snapshot includes latest status of each issue, plus it relies on the future knowledge. E.g. if issue was in backlog on monday, in qa on thursday - it will be recorded as "qa". If issue was in review on tuesday and resolved on friday, but - we know - in the future it was reopened - issue would be not counted as resolved in the given week.
"accepted on demo" category is a built-in one and it simply attributes issue to the timeframe, when "accepted on demo" was set last time.

### Google Spreadsheet Writer

Primary responsibility is to write processed & aggregated data into Google Sheets.
It also shares spreadsheets with Developer or other people as well - it is configurable.

There are two variants of classes - GspreadTeamWriter & GspreadDeveloperWrite dedicated to work with Team and Developer objects respectively
