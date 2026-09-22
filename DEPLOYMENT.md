# Free public demo deployment

This deployment serves React and FastAPI together on one Render Free web service, with PostgreSQL on the Neon Free plan. Your laptop can be off. The public URL is assigned by Render after deployment; no custom domain is needed.

## Account setup

1. Sign in to Render and Neon with your own account. Select only free plans and do not add a payment method for this demo.
2. In Neon, create a Free PostgreSQL project named `weather-aggregator`.
3. Copy its pooled PostgreSQL connection string, including its TLS parameters such as `sslmode=require`. Treat it as a password. Do not commit it to GitHub or paste it into documentation.
4. In Render, connect the private GitHub repository `manastewari/weather-aggregator`. Grant access to this repository.
5. Create a Blueprint from the repository. `render.yaml` selects the Free plan and `Dockerfile.hosted`.
6. When prompted for `DATABASE_URL`, enter the Neon connection string in Render's environment settings.
7. Deploy and use the HTTPS URL shown by Render. Verify that fetching a city and viewing history both work.

Alternatively, create a Web Service manually, choose Docker and the Free instance type, set Dockerfile Path to `./Dockerfile.hosted`, Health Check Path to `/healthz`, and add the same `DATABASE_URL` environment variable.

## What changes for hosting?

`weather/hosted.py` assembles the same API and mounts the built frontend after its API routes. `Dockerfile.hosted` builds React and packages the UI with FastAPI in one container. The existing local Compose setup is unchanged. The hosted entry point requires PostgreSQL so an accidental missing setting cannot create a temporary SQLite database.

The hosted database starts empty; local Docker readings are not automatically uploaded. Visitors share the demo's saved weather history and can add readings. There are no private user accounts in this assignment app.

## Free-plan limits

Render's Free web service sleeps after 15 minutes without incoming traffic and can take about a minute to wake up. Monthly free quotas apply. Without a payment method, services can be suspended rather than incur usage charges. Neon has its own free storage and compute quotas; remain on its Free plan. This is a demo setup, not an uptime guarantee.

Do not use Render's Free PostgreSQL for lasting demo data: it expires after 30 days. The separate Neon database keeps application data outside Render's temporary filesystem.

Sources checked September 22, 2026: https://render.com/docs/free, https://render.com/docs/faq, https://neon.com/pricing.

Deployment is not complete until the accounts are connected, the database setting is supplied, and the live URL passes a fetch-and-history check.
