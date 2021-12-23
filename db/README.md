# YCC Hull / DB

The new system uses the existing Oracle database (hosted at CERN). This is mainly for migration reasons.

To connect to the database programmatically (both local and remote) you will need to
install [Oracle Instant Client](https://www.oracle.com/uk/database/technologies/instant-client/downloads.html).

To inspect the database, best is to use [SQL Developer](https://www.oracle.com/tools/downloads/sqldev-downloads.html).
Modern IDEs also have data browser extensions.

## Local Instance

You can run a local instance of Oracle XE via Docker - the recommended approach is to use the Docker Compose file in
this directory.
