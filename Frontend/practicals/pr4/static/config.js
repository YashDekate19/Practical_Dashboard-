// Centralized Render Backend API Configuration
// Replace this URL with your deployed Render Flask service URL:
const BACKEND_API_URL = "https://auth-flask-api.onrender.com";

// Expose globally for single API base URL configuration across all requests
window.API_BASE_URL = window.API_BASE_URL || BACKEND_API_URL;
