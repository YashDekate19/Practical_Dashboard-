# Practical 4 - Flask + MySQL deployment files for Render

This folder contains the Flask API from the supplied dashboard project, its templates/static files, the MySQL schema, and a Docker image definition for a self-managed MySQL server.

## Important
Render does not provide managed MySQL. This package runs MySQL in a private Docker service with a persistent disk. You are responsible for backups, updates, security, and monitoring. For a production application, Render managed PostgreSQL is generally easier to operate, but that requires changing the Python database driver and SQL setup.

## Deploy using Render Blueprint

1. Upload this `render-backend` folder to a GitHub repository. Keep `render.yaml` at the repository root.
2. In Render, choose **New + → Blueprint** and connect the repository.
3. Render will ask for `MYSQL_PASSWORD` and `MYSQL_ROOT_PASSWORD`. Set strong, different passwords. Save the `MYSQL_PASSWORD` value because you must enter the exact same value for the Flask service's `DB_PASSWORD`.
4. Review the two services and create them. The MySQL service uses a persistent disk at `/var/lib/mysql`; do not remove that disk or the database data will be lost.
5. In the `auth-flask-api` service, set `DB_PASSWORD` to the same password entered for `MYSQL_PASSWORD`.
6. After deployment, open `https://YOUR-FLASK-SERVICE.onrender.com/api/test-db`. A successful response should report `MySQL connection successful`.

## Environment variables

Flask service:
- `DB_HOST=auth-mysql` (Render private service hostname)
- `DB_PORT=3306`
- `DB_NAME=authentication_db`
- `DB_USER=auth_user`
- `DB_PASSWORD` = same value as MySQL `MYSQL_PASSWORD`
- `FRONTEND_ORIGIN` = your Netlify site origin, e.g. `https://your-site.netlify.app` (or `*` temporarily for testing)

MySQL service:
- `MYSQL_DATABASE=authentication_db`
- `MYSQL_USER=auth_user`
- `MYSQL_PASSWORD` = strong password
- `MYSQL_ROOT_PASSWORD` = a different strong password

## Local run

Create a virtual environment, install requirements, create the database using `schema.sql`, set the DB environment variables, then run:

```bash
pip install -r requirements.txt
python app.py
```

## API endpoints retained
- `GET /api/test-db`
- `POST /api/register` with JSON `{ "name": "Example", "email": "example@mail.com", "password": "secret123" }`
- `POST /api/login` with JSON `{ "email": "example@mail.com", "password": "secret123" }`
- `GET /api/users`

Passwords are stored as bcrypt hashes. Do not expose `/api/users` publicly in a real production app; add admin authentication/authorization before using it with real users.

## Connect your Netlify frontend
Update the Practical 4 frontend API calls to use the deployed Flask base URL, for example:
`https://YOUR-FLASK-SERVICE.onrender.com/api/login`

Do not put database credentials in frontend JavaScript. Only the Flask service should connect to MySQL.
