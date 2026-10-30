// Verify Vite's build-time API URL before publishing a static staging bundle.
const value = (process.env.VITE_API_URL ?? "").trim();
let url;
try {
  url = new URL(value);
} catch {
  console.error("Staging: VITE_API_URL must be a complete public HTTPS URL.");
  process.exit(1);
}
if (url.protocol !== "https:" || !url.hostname || url.hostname === "localhost" || url.hostname === "127.0.0.1" || url.username || url.password) {
  console.error("Staging: VITE_API_URL cannot point to localhost or include credentials.");
  process.exit(1);
}
console.log("Staging: HTTPS API endpoint configured.");
