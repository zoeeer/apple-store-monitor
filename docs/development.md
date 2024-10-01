# Development

## Tech Stack

- Python 3.12
- Database: PostgreSQL 17.0
- ORM: [peewee](http://docs.peewee-orm.com/en/latest/)

## Development Notes

### 1. Database Tables

#### Migrations Management

Use the database migration tool: [peewee-migrations](https://github.com/aachurin/peewee_migrations)

- Build update content

```sh
# If the database table structure (Models) has changed, execute this command to generate migration files
pem watch --serialize

# Migration files are located in db/migrations, please add them to git management
```

- Execute updates on the database

```sh
pem migrate # Update to the latest version

# Update to a specific version:
pem migrate 0001 # Update to version 0001
```

- Add new tables

```sh
# If new tables (new Models) are added, execute this command to inform peewee-migrations to monitor their changes
# Otherwise, pem watch will not detect these tables
pem add models.SomeModel
```

- Configuration file: `migrations.json`
