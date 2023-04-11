# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
