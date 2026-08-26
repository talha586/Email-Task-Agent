# Backend image: Django (BackEnd/) + the Agent package (Agent/).
# Uses PYTHONPATH rather than `pip install -e ./Agent`, since that avoids
# any dependency on Agent/pyproject.toml being configured for packaging —
# same reasoning as the PYTHONPATH fallback used for the Windows setup.

FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies first so this layer is cached across builds
# unless requirements.txt itself changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Agent package and the Django project.
COPY Agent/ ./Agent/
COPY manage.py .
COPY BackEnd/ ./BackEnd/

ENV PYTHONPATH=/app/Agent/src

EXPOSE 8000

# Apply migrations, then start the server. Fine for a demo/dev deployment;
# swap runserver for gunicorn if this ever needs to handle real traffic.
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]