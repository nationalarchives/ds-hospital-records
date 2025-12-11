# Data Migration Command

## Overview

The `migrate_data` management command migrates hospital records data from a legacy MSSQL database to the Django PostgreSQL database. It handles the complete migration of hospitals, repositories, records information, and all related lookup tables while preserving original IDs and timestamps.

## Usage

```bash
python manage.py migrate_data [options]
```

Or with the Docker environment:

```bash
docker compose exec app poetry run python manage.py migrate_data [options]
```

## Command Options

### Connection Parameters

All connection parameters can be provided via command-line arguments or environment variables.

| Option       | Environment Variable | Default | Description                         |
| ------------ | -------------------- | ------- | ----------------------------------- |
| `--host`     | `MSSQL_HOST`         | -       | MSSQL server hostname or IP address |
| `--port`     | `MSSQL_PORT`         | `1433`  | MSSQL server port                   |
| `--database` | `MSSQL_DATABASE`     | -       | MSSQL database name                 |
| `--user`     | `MSSQL_USER`         | -       | MSSQL username                      |
| `--password` | `MSSQL_PASSWORD`     | -       | MSSQL password                      |

**Required parameters:** `host`, `database`, `user`, `password`

### Operational Options

| Option      | Description                                                                                                                     |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `--dry-run` | Run the migration without saving any data to the database. Useful for testing the connection and seeing what would be migrated. |
| `--clear`   | Clear all existing data before migration. **WARNING:** This permanently deletes all records from the database.                  |

## Examples

### Basic Migration

Migrate all data using environment variables for connection details:

```bash
python manage.py migrate_data
```

### Dry Run

Test the migration without making any changes:

```bash
python manage.py migrate_data --dry-run
```

### Clear and Re-migrate

Delete all existing data and perform a fresh migration:

```bash
python manage.py migrate_data --clear
```

### Explicit Connection Parameters

Provide connection details directly:

```bash
python manage.py migrate_data \
  --host mssql.example.com \
  --database HospitalRecords \
  --user migration_user \
  --password 'secure_password'
```

## Migration Process

The command migrates data in the following order to maintain referential integrity:

1. **Lookup Tables Population** - Pre-populates Status, Type, FindingAids, and FindingAidsLocation lookup tables
2. **Counties** - Pre-1974, Post-1974, and Post-1996 county reference tables
3. **Authorities** - Regional boards, management committees, and regional/district authorities (pre/post 1982)
4. **Repositories** - Repository records with contact information
5. **Hospitals** - Hospital records with addresses, dates, and relationships
6. **Records Information** - Folder records linking hospitals to repositories with date ranges

## Data Mapping

### Source Tables

The command reads from the following MSSQL tables:

- `tblRefCountyPre74`, `tblRefCountyPost74`, `tblRefCountyPost96`
- `tblRefRegionalBoard1948`
- `tblRefManagementCommittee1948`
- `tblRefRegionalAuthority1974`, `tblRefRegionalAuthority1982`
- `tblRefDistrictAuthority1974`, `tblRefDistrictAuthority1982`
- `tblRepository`
- `tblHospital`
- `tblFolder`

### Key Features

#### ID Preservation

Original IDs from the MSSQL database are preserved in the Django database:

- Hospital IDs from `Hospital_No`
- Repository IDs from `Repository_No`
- Folder IDs from `Folder_No`

#### Timestamp Handling

The command preserves original creation and update timestamps:

- Uses `InputDate` for `created_at`
- Uses `LastUpdatedDate` for `last_updated_at`
- Falls back to available date if one is missing
- Automatically converts naive datetimes to timezone-aware

#### Boolean to Many-to-Many Conversion

Boolean flags in the MSSQL database are converted to many-to-many relationships:

- Hospital pre/post 1948 status flags → `Pre1948Status` and `Post1948Status` relationships
- Hospital pre/post 1948 type flags → `Pre1948Type` and `Post1948Type` relationships
- Finding aids flags → `FindingAids` relationships
- Finding aids location flags → `FindingAidsLocation` relationships

#### Special Value Handling

- `RepositoryCode = "BLANK"` → `NULL` in database
- Foreign key `ID = 1` (placeholder value) → `NULL`
- Missing foreign key references → `NULL` with warning message

## Output

The command provides detailed progress information:

```
Connected to MSSQL database: HospitalRecords
Ensuring lookup tables are populated...
Lookup tables populated
Migrating Pre-1974 Counties...
Found 45 Pre-1974 Counties
Pre-1974 Counties: 45 created
...
Hospitals: 1250 created, 0 updated
...
Migration completed successfully
```

## Error Handling

The command handles various error scenarios:

- **Missing Connection Parameters**: Fails early with clear error message
- **Connection Failures**: Reports connection errors before attempting migration
- **Missing Foreign Keys**: Logs warnings and sets relationships to NULL
- **Invalid Data**: Continues migration, logging errors for individual records

## Troubleshooting

### Connection Issues

If you encounter connection errors:

1. Verify MSSQL server is accessible from your network
2. Check firewall rules allow connections on the MSSQL port
3. Confirm credentials are correct
4. Ensure the database name is spelled correctly

### Partial Migration

If migration fails partway through:

1. Use `--clear` to remove partial data
2. Check the error message for the specific issue
3. Fix any data issues in the source database
4. Re-run the migration

### Performance Issues

For large datasets:

- Run during off-peak hours
- Consider migrating in stages if possible
- Monitor database connection limits
- Ensure adequate database resources

## Related Models

For model definitions and field details, see:

- [app/hospitaldetails/models/hospital.py](../app/hospitaldetails/models/hospital.py)
- [app/hospitaldetails/models/repository.py](../app/hospitaldetails/models/repository.py)
- [app/hospitaldetails/models/recordsinfo.py](../app/hospitaldetails/models/recordsinfo.py)

## Development

The migration command is located at:

```
app/hospitaldetails/management/commands/migrate_data.py
```

Key helper methods:

- `make_timezone_aware(dt)` - Timezone conversion
- `prepare_timestamps(input_date, last_updated_date)` - Timestamp preparation
- `set_foreign_key_if_valid(obj, field_name, fk_id, model_class, error_label)` - FK validation
- `add_m2m_if_true(obj, m2m_field, condition, model_class, value)` - M2M relationship management
- `migrate_lookup_table(cursor, dry_run, config)` - Generic lookup table migration
