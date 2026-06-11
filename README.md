# Volunteer Resource Download Portal

Full-stack portal for student volunteers to log in, browse PDF/DOCX resources, and download volunteer checklists or educational materials.

## Backend

```bash
cd backend
uv sync
uv run python backend/manage.py migrate
uv run python backend/manage.py createsuperuser
uv run python backend/manage.py runserver 8000
```

Upload PDF or DOCX files at `http://localhost:8000/admin/`.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173/` and sign in with a Django user account.

## Notes

- PDF and DOCX resources are managed through Django admin.
- Volunteers must be authenticated before they can list or download resources.
- The React dev server expects the Django API at `http://localhost:8000`.
