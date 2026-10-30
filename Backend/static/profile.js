document.addEventListener("DOMContentLoaded", async () => {

    const userData = localStorage.getItem("user");

    if (!userData) {
        window.location.href = "/";
        return;
    }

    let user;
    try {
        user = JSON.parse(userData);
    } catch (e) {
        localStorage.removeItem("user");
        window.location.href = "/";
        return;
    }

    const userName = document.getElementById("userName");
    const profileName = document.getElementById("profileName");
    const profileEmail = document.getElementById("profileEmail");

    if (userName && user.name) {
        userName.textContent = user.name;
    }

    if (profileName && user.name) {
        profileName.textContent = user.name;
    }

    if (profileEmail && user.email) {
        profileEmail.textContent = user.email;
    }

    // Refresh user profile details from backend
    if (user && (user.id || user.email)) {
        try {
            const token = localStorage.getItem("auth_token");
            const headers = { "Content-Type": "application/json" };
            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const query = user.id ? `id=${encodeURIComponent(user.id)}` : `email=${encodeURIComponent(user.email)}`;
            const response = await fetch(`/api/profile?${query}`, { headers });
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.user) {
                    if (userName && data.user.name) userName.textContent = data.user.name;
                    if (profileName && data.user.name) profileName.textContent = data.user.name;
                    if (profileEmail && data.user.email) profileEmail.textContent = data.user.email;
                    localStorage.setItem("user", JSON.stringify(data.user));
                }
            }
        } catch (err) {
            console.warn("Could not refresh profile data:", err);
        }
    }

    const logoutBtn = document.getElementById("logoutBtn");

    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            localStorage.removeItem("user");
            localStorage.removeItem("auth_token");
            window.location.href = "/";
        });
    }

});