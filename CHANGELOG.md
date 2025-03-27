# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Email notifications for helper tasks:
  - When someone signs up
  - When a task is marked as done
  - When a task is validated
  - When a task is upcoming (2 weeks, 3 days ahead and on the day of the task)
  - When a task is overdue (only 1 week after for shifts)
  - When a task is updated and a notification is requested

### Changed

- Allow editors to change timing of helper tasks
- Do not allow changing the year of the task if anyone has signed up
- Hierarchical `config.json` for better readability
- UTF-8 log file


## [1.1.0] - 2025-03-16

### Added

- Year-aware helper tasks
- Helper task validation
- Consistent time zone handling for datetime properties

### Changed

- Better error reporting for task timing issues
- Upgrade to Python 3.12
- Upgrade to Poetry 2
- Dependency upgrades (2025-03), notable:
  - OracleDB adapter 3.0.0
  - sqlacodegen 3.0.0 (which supports SQLAchemy 2.x)
- Move production code to `src/`
- For containerisation, use Poetry to generate a `requirements.txt` file for micropipenv
- Switch to python-oracledb thick mode
- Prepare for Keycloak 26

## [1.0.0] - 2024-01-30

### Changed

- Do not send long description on the task list API endpoint
- Dependency upgrades (2024-01), notable:
  - Pydantic V2
  - OracleDB adapter 2.0.1 & migrate to full async usage
- Upgrade to Python 3.11
- Update REST API endpoints to /v1/

## [0.4.0] - 2023-06-26

### Changed

- Streamline DB field naming, apply new naming to entities, model and API

## [0.3.0] - 2023-05-01

### Added

- Add support for DB entities: audit log entries, Helpers App permissions
- Add test data: Helpers App permissions
- Add to helpers controller: create helper task
- Add controller: licences
- Add API endpoints:
  - POST create helper task
  - PUT update helper task
  - GET licence infos
- Sanitise inputs, allow controlled HTML inputs
- Add support for SQLite database
  - Streamline entity declarations
  - Streamline test data generation
- Add testing facilities: fake authentication, test database

### Changed

- Replies contain unpublished tasks if the user has the permission to see them
- Use Python 3.9 type annotations where possible
- Extract the User entity from the auth module to facilitate testing
- Rename configuration property `dbUrl` to `databaseUrl`

## [0.2.0] - 2023-04-12

### Added

- Add support for DB entities: licences, helpers
- Add DTOs: licence info, helpers
- Add test data: helpers
- Add controller: helpers
- Add API endpoints:
  - GET helper task categories
  - GET helper tasks
  - GET helper task by ID
  - POST sign up as captain to a helper task
  - POST sign up as helper to a helper task

## [0.1.0] - 2023-04-05

### Added

- Initial version of the backend service (Wrap up PoC)
- Add support for DB entities: members, users, boats, payment records and holidays
- Add DTOs: members, users, boats, payment records and holidays
- Add API endpoints for member search and some other entities
- Oracle DB integration
- Keycloak integration
- Test data generator
- Deployment on CERN OKD TEST

[unreleased]: https://github.com/Yachting-Club-CERN/ycc-hull/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/Yachting-Club-CERN/ycc-hull/releases/tag/v1.1.0
[1.0.0]: https://github.com/Yachting-Club-CERN/ycc-hull/releases/tag/v1.0.0
[0.4.0]: https://github.com/Yachting-Club-CERN/ycc-hull/releases/tag/v0.4.0
[0.3.0]: https://github.com/Yachting-Club-CERN/ycc-hull/releases/tag/v0.3.0
[0.2.0]: https://github.com/Yachting-Club-CERN/ycc-hull/releases/tag/v0.2.0
[0.1.0]: https://github.com/Yachting-Club-CERN/ycc-hull/releases/tag/v0.1.0
