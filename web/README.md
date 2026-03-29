# EarlyPredict Web

Publishing layer for EarlyPredict by Monarch Castle Intelligence.

## Stack

- Next.js App Router
- TypeScript
- Tailwind CSS
- MDX
- Recharts

## Local development

```bash
npm install
npm run content:validate
npm run dev
```

## Key routes

- `/`
- `/forecasts`
- `/countries`
- `/countries/[slug]`
- `/reports`
- `/reports/[slug]`
- `/methodology`
- `/methodology/[slug]`
- `/about`

## Content structure

```text
content/
  reports/
  methodology/
```

Each MDX file exports a `frontmatter` object used for route metadata and listing pages.

## Build checks

```bash
npm run content:validate
npm run lint
npm run build
```
