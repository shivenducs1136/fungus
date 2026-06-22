# Frontend Portal (React + Vite)

React portal for managing architectural context stored by Jira IDs.

## Features

- Search by Jira combination key (for example `[ERP-24][ERP-25]`) or by single Jira ID.
- Create, read, update, and delete context entries.
- Client-side filtering by text and Jira ID.
- Pagination with adjustable page size.

## Configuration

Set API target URL with:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

If omitted, it defaults to `http://127.0.0.1:8000`.

## Run

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Test scripts

```bash
npm run test
npm run test:watch
npm run test:coverage
```
