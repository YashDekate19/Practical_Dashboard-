# Netlify Deployment - Web Development Practicals Dashboard

## Deploy on Netlify

### Option 1: Git Repository Connection (Recommended)
1. Push this repository to GitHub.
2. In the Netlify Dashboard, select **Add new site → Import an existing project**.
3. Select your GitHub repository.
4. Netlify will automatically detect `netlify.toml` in the repository root:
   - **Base directory**: `Frontend`
   - **Publish directory**: `.`
   - **Build command**: (None required - static assets pre-bundled)
5. Click **Deploy Site**.

### Option 2: Netlify Drop / Manual Deploy
1. Drag and drop the `Frontend` folder directly into https://app.netlify.com/drop.
2. Netlify will deploy immediately.

## Connecting Practical 4 to Your Render Backend

Practical 4 (Authentication & Profile System) connects to the Flask API hosted on Render.

To update the Render API base URL:
1. Open `Frontend/practicals/pr4/static/config.js`.
2. Update `BACKEND_API_URL` to match your deployed Render service URL:
   ```javascript
   const BACKEND_API_URL = "https://auth-flask-api.onrender.com";
   ```
3. Commit and push to update Netlify automatically.

## Included Practicals
- **Main Dashboard**: Real-time search, category filtering, embedded preview modal, and responsive design.
- **Practical 1 (Tasty Restaurant)**: Responsive restaurant catalog, menu cards, and hero section.
- **Practical 2 (ShopEasy E-Commerce)**: Electronics storefront with grid layout and special offers.
- **Practical 3 (Personal Portfolio)**: Developer portfolio with skills, projects, and contact info.
- **Practical 4 (Auth & Profile System)**: Full-stack login, registration, and profile views communicating with Flask & MySQL.
- **Practical 5 (The Daily Times)**: Editorial multi-column newspaper layout.
- **Practical 6 (Student Portal)**: Pre-compiled production React 19 + Vite SPA.

