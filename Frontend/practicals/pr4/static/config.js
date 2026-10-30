// Centralized Render Backend API Configuration
// Automatically detects local development vs production deployment on Netlify
const isLocal = typeof window !== "undefined" && (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1" ||
    window.location.protocol === "file:"
);

const BACKEND_API_URL = isLocal
    ? "http://localhost:5000"
    : "https://auth-flask-api.onrender.com";

// Expose globally for single API base URL configuration across all requests
window.API_BASE_URL = window.API_BASE_URL || BACKEND_API_URL;

