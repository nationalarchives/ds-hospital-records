# ARCHON links and codes

## Overview

ARCHON is the national directory of archives managed by The National Archives. In this application, repositories can store an ARCHON code, which is used to link out to the authoritative repository page on Discovery.

- Field: `Repository.archon_code`
- Derived URL: `Repository.archon_url`
- External site: `https://discovery.nationalarchives.gov.uk/`

## How the link is constructed

When a repository has an `archon_code`, the `archon_url` property builds a Discovery URL using the `_ref` query parameter.

Example:

```
Repository.archon_code = 123
Repository.archon_url = https://discovery.nationalarchives.gov.uk/details/a?_ref=123
```

## UI behavior

- Repository detail pages redirect to `archon_url` when it exists.
- Repository names in record listings link to `archon_url` when it exists; otherwise they link to the local repository detail page.

## Data expectations

- `archon_code` is optional.
- When missing, the application renders local repository details only.
- When present, it is treated as the canonical link to repository contact information.
