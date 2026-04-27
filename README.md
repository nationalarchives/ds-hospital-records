# TNA Python Flask Application

## Quickstart

```sh
# Build and start the container
docker compose up -d
```

### Add the static assets

During the first time install, your `app/static/assets` directory will be empty.

As you mount the project directory to the `/app` volume, the static assets from TNA Frontend installed inside the container will be "overwritten" by your empty directory.

To add back in the static assets, run:

```sh
docker compose exec app cp -r /app/node_modules/@nationalarchives/frontend/nationalarchives/assets /app/app/static
```

### Run tests

```sh
docker compose exec app poetry run pytest --ds=config.settings.test
```

### Format and lint code

```sh
docker compose exec app format
```

## Environment variables

In addition to the [base Docker image variables](https://github.com/nationalarchives/docker/blob/main/docker/tna-python/README.md#environment-variables), this application has support for:

| Variable                 | Purpose                                                   | Default                                                   |
| ------------------------ | --------------------------------------------------------- | --------------------------------------------------------- |
| `DJANGO_SETTINGS_MODULE` | The configuration to use                                  | `config.settings.production`                              |
| `ALLOWED_HOSTS`          | A comma-separated list of allowed hosts                   | _none_ on production and staging, `*` on develop and test |
| `USE_X_FORWARDED_HOST`   | Use the `X-Forwarded-Host` header in preference to `Host` | `False`                                                   |
| `DEBUG`                  | If true, allow debugging                                  | `False`                                                   |
| `COOKIE_DOMAIN`          | The domain to save cookie preferences against             | `.nationalarchives.gov.uk`                                |
| `COOKIE_PREFERENCES_URL` | The URL for changing cookie preferences                   | `/cookies/`                                               |
| `COOKIE_PREFERENCES_KEY` | The URL for changing cookie preferences                   | `dontShowCookieNotice`                                    |
| `DATABASE_NAME`          | The name of the Postgres database                         | _none_                                                    |
| `DATABASE_USER`          | The username needed to access the Postgres database       | _none_                                                    |
| `DATABASE_PASSWORD`      | The password needed to access the Postgres database       | _none_                                                    |
| `DATABASE_HOST`          | The Postgres database host                                | _none_                                                    |
| `DATABASE_PORT`          | The Postgres database port                                | `5432`                                                    |
| `CSP_IMG_SRC`            | A comma separated list of CSP rules for `img-src`         | `'self'`                                                  |
| `CSP_SCRIPT_SRC`         | A comma separated list of CSP rules for `script-src`      | `'self'`                                                  |
| `CSP_STYLE_SRC`          | A comma separated list of CSP rules for `style-src`       | `'self'`                                                  |
| `CSP_FONT_SRC`           | A comma separated list of CSP rules for `font-src`        | `'self'`                                                  |
| `CSP_CONNECT_SRC`        | A comma separated list of CSP rules for `connect-src`     | `'self'`                                                  |
| `CSP_MEDIA_SRC`          | A comma separated list of CSP rules for `media-src`       | `'self'`                                                  |
| `CSP_WORKER_SRC`         | A comma separated list of CSP rules for `worker-src`      | `'self'`                                                  |
| `CSP_FRAME_SRC`          | A comma separated list of CSP rules for `frame-src`       | `'self'`                                                  |
| `CSP_REPORT_URL`         | The URL to report CSP violations to                       | _none_                                                    |
| `GA4_ID`                 | The Google Analytics 4 ID                                 | _none_                                                    |
| `MSSQL_HOST`             | The MSSQL server hostname (for data migration)            | _none_                                                    |
| `MSSQL_PORT`             | The MSSQL server port (for data migration)                | `1433`                                                    |
| `MSSQL_DATABASE`         | The MSSQL database name (for data migration)              | _none_                                                    |
| `MSSQL_USER`             | The MSSQL username (for data migration)                   | _none_                                                    |
| `MSSQL_PASSWORD`         | The MSSQL password (for data migration)                   | _none_                                                    |

## Data Migration

This project includes a management command to migrate hospital records data from a legacy MSSQL database to PostgreSQL.

### Prerequisites

1. Ensure you have access to the source MSSQL database
2. Configure the MSSQL connection parameters (see environment variables above)
3. Run Django migrations to set up the database schema:

```sh
docker compose exec app poetry run python manage.py migrate
```

### Migration Steps

#### 1. Set up environment variables

Add the MSSQL connection details to your environment or `.env` file:

```sh
MSSQL_HOST=your-mssql-server.example.com
MSSQL_DATABASE=HospitalRecords
MSSQL_USER=migration_user
MSSQL_PASSWORD=your_secure_password
```

#### 2. Test the migration (dry run)

Before migrating data, test the connection and see what would be migrated:

```sh
docker compose exec app poetry run python manage.py migrate_data --dry-run
```

#### 3. Run the migration

Migrate all data from MSSQL to PostgreSQL:

```sh
docker compose exec app poetry run python manage.py migrate_data
```

#### 4. Clear and re-migrate (if needed)

If you need to start fresh and re-migrate all data:

```sh
docker compose exec app poetry run python manage.py migrate_data --clear
```

**Warning:** The `--clear` flag will permanently delete all existing hospital records data.

### What Gets Migrated

The migration command handles:

- **Lookup tables**: Pre/Post 1948 Status and Type, Finding Aids, Counties, Authorities
- **Repositories**: Archive and repository information
- **Hospitals**: Hospital records with addresses, dates, and historical information
- **Records Info**: Folder records linking hospitals to repositories with date ranges

### Migration Details

- Original IDs from MSSQL are preserved
- Timestamps (creation and update dates) are maintained
- Boolean flags are converted to many-to-many relationships
- Special values like `"BLANK"` are converted to `NULL`
- The migration runs in a specific order to maintain referential integrity

For complete documentation, see [docs/data-migration.md](docs/data-migration.md).
