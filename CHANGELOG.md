# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

TODO testing
TODO run tests on CI
TODO coverage on CI?

### Added

- Add support for DB entities: audit log entry, Helpers App permissions
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
  - POST subscribe as captain to a helper task
  - POST subscribe as helper to a helper task

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

[unreleased]: https://github.com/Yachting-Club-CERN/ycc-hull/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Yachting-Club-CERN/ycc-hull/releases/tag/v0.2.0
[0.1.0]: https://github.com/Yachting-Club-CERN/ycc-hull/releases/tag/v0.1.0
