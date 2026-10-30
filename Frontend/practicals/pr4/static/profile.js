// Configurable Render backend base URL
const API_BASE_URL = (typeof window !== "undefined" && window.API_BASE_URL)
    ? window.API_BASE_URL.replace(/\/+$/, "")
    : "https://auth-flask-api.onrender.com";

document.addEventListener("DOMContentLoaded", async () => {

    const userData = localStorage.getItem("user");

    if (!userData) {
        window.location.href = "index.html";
        return;
    }

    let user;
    try {
        user = JSON.parse(userData);
    } catch (e) {
        localStorage.removeItem("user");
        window.location.href = "index.html";
        return;
    }

    const userName = document.getElementById("userName");
    const profileEmail = document.getElementById("profileEmail");
    const profileId = document.getElementById("profileId");
    const backendStatus = document.getElementById("backendStatus");

    // Display cached session user data immediately
    if (userName && user.name) userName.textContent = user.name;
    if (profileEmail && user.email) profileEmail.textContent = user.email;
    if (profileId && user.id) profileId.textContent = `#${user.id}`;

    // Communicate with Render backend to verify and refresh profile
    if (user && (user.id || user.email)) {
        try {
            const token = localStorage.getItem("auth_token");
            const headers = { "Content-Type": "application/json" };
            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const query = user.id
                ? `id=${encodeURIComponent(user.id)}`
                : `email=${encodeURIComponent(user.email)}`;

            const response = await fetch(`${API_BASE_URL}/api/profile?${query}`, { headers });

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.user) {
                    const freshUser = data.user;
                    if (userName && freshUser.name) userName.textContent = freshUser.name;
                    if (profileEmail && freshUser.email) profileEmail.textContent = freshUser.email;
                    if (profileId && freshUser.id) profileId.textContent = `#${freshUser.id}`;
                    if (backendStatus) {
                        backendStatus.textContent = "Render & MySQL Verified";
                        backendStatus.style.color = "#059669";
                    }
                    localStorage.setItem("user", JSON.stringify(freshUser));
                }
            } else if (response.status === 401 || response.status === 403) {
                if (backendStatus) {
                    backendStatus.textContent = "Session Expired";
                    backendStatus.style.color = "#dc2626";
                }
            } else if (backendStatus) {
                backendStatus.textContent = "Cached (Backend Unreachable)";
                backendStatus.style.color = "#d97706";
            }
        } catch (err) {
            console.warn("Could not reach Render backend to refresh profile:", err);
            if (backendStatus) {
                backendStatus.textContent = "Offline Session";
                backendStatus.style.color = "#d97706";
            }
        }
    }

    // Logout Handler
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            localStorage.removeItem("user");
            localStorage.removeItem("auth_token");
            window.location.href = "index.html";
        });
    }

});
