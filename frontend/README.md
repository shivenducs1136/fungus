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

## Build & Release (with Sitemap)

To build the static assets for production:

```bash
npm run build
```

This will run TypeScript type checking (`tsc -b`) and then build the application with Vite into the `dist/` folder.

**Sitemap Generation**: During the build process, `vite-plugin-sitemap` will automatically generate `sitemap.xml` and `robots.txt` in the `dist/` output directory. This ensures the landing page, docs, and dashboard routes are easily indexable by search engines.

*Note: Ensure the `hostname` in `vite.config.ts` is updated to your production domain for the sitemap to be fully valid.*

## Test scripts

```bash
npm run test
npm run test:watch
npm run test:coverage
```
