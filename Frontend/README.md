# Netlify-ready Web Development Practicals Dashboard

## Deploy on Netlify
1. Extract this ZIP file on your computer.
2. Open https://app.netlify.com/drop and sign in.
3. Drag the extracted `netlify-ready-dashboard` folder (the folder containing `index.html`) into the Netlify Drop area.
4. Wait for deployment. Open the generated Netlify URL.

Alternatively, push this folder to GitHub and import that repository in Netlify. No build command is needed; the publish directory is `.`.

## Included
- Main dashboard with search and filters
- Practical 1: Tasty Restaurant
- Practical 2: ShopEasy E-Commerce
- Practical 3: Personal Developer Portfolio
- Practical 4: Login/registration UI preview
- Practical 5: The Daily Times News Portal
- Practical 6: Built React production site

## Important hosting limitation
Netlify serves static sites and can host the built React frontend. Practical 4's included login/register page is only a visual frontend preview. Its Flask server and MySQL database are not hosted by this ZIP, so registration, login, and database-backed profile features will not work until the backend is separately deployed and configured with a hosted database. The dashboard's local service start/stop controls were removed for the static deployment.
