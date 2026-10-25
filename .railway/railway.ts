import { defineRailway, github, postgres, preserve, project, service, volume } from "railway/iac";

export default defineRailway(() => {
  const Postgres = postgres("Postgres", { region: "europe-west4-drams3a" });
  Postgres.networking = { privateNetworkEndpoint: "postgres" };
  const postgresVolume = volume("postgres-volume", { alerts: { usage: { "100": {}, "80": {}, "95": {} } }, allowOnlineResize: true, region: "europe-west4-drams3a", sizeMB: 5000 });
  const backend = service("backend", {
    source: github("DomasB/polito-log", { branch: "main", checkSuites: true, rootDirectory: "/backend" }),
    build: { builder: "RAILPACK", watchPatterns: ["/backend/**"] },
    preDeploy: "python -m app.cli migrate",
    healthcheck: "/",
    healthcheckTimeout: 100,
    replicas: { "europe-west4-drams3a": 1 },
    domains: [{ domain: "api.polito-log.lt", port: 8000 }],
    networking: { privateNetworkEndpoint: "polito-log" },
    env: { BREVO_API_KEY: preserve(), DATABASE_URL: preserve(), DEBUG: preserve(), ENVIRONMENT: preserve(), FRONTEND_URL: preserve(), JWT_SECRET_KEY: preserve(), PORT: preserve(), VITE_API_URL: preserve() },
  });
  const frontend = service("frontend", {
    source: github("DomasB/polito-log", { branch: "main", checkSuites: true, rootDirectory: "/frontend" }),
    build: { buildCommand: "npm run build", builder: "RAILPACK", watchPatterns: ["/frontend/**"] },
    start: "",
    healthcheck: "/health",
    healthcheckTimeout: 100,
    preDeploy: [],
    replicas: { "europe-west4-drams3a": 1 },
    domains: ["polito-log.lt", "www.polito-log.lt"],
    networking: { privateNetworkEndpoint: "polito-log-frontend" },
    env: { VITE_API_URL: preserve(), VITE_APP_URL: preserve() },
  });

  return project("polito-log", {
    variables: { managed: true },
    resources: [Postgres, backend, frontend, postgresVolume],
  });
});
