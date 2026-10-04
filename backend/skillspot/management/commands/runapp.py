"""
Production/local container boot: migrate → optional superuser → Celery + Daphne.

Usage:
    python manage.py runapp
"""
import os
import signal
import subprocess
import sys
import time

from django.core.management import BaseCommand, call_command
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Run migrations, start Celery worker, then Daphne (app boot for Docker).'

    def handle(self, *args, **options):
        self._wait_for_db_and_migrate()
        self._maybe_create_superuser()

        concurrency = os.environ.get('CELERY_CONCURRENCY', '1')
        port = os.environ.get('PORT', '8000')

        self.stdout.write(self.style.NOTICE('Starting Celery worker...'))
        celery = subprocess.Popen(
            [
                'celery',
                '-A',
                'skillspot',
                'worker',
                '-l',
                'info',
                f'--concurrency={concurrency}',
            ],
        )

        def _shutdown(signum, _frame):
            self.stdout.write(self.style.NOTICE('Shutting down...'))
            celery.terminate()
            try:
                celery.wait(timeout=15)
            except subprocess.TimeoutExpired:
                celery.kill()
            sys.exit(0)

        signal.signal(signal.SIGTERM, _shutdown)
        signal.signal(signal.SIGINT, _shutdown)

        self.stdout.write(self.style.SUCCESS(f'Starting Daphne on 0.0.0.0:{port}...'))
        try:
            daphne = subprocess.run(
                [
                    'daphne',
                    '-b',
                    '0.0.0.0',
                    '-p',
                    str(port),
                    'skillspot.asgi:application',
                ],
                check=False,
            )
            raise SystemExit(daphne.returncode)
        finally:
            celery.terminate()
            try:
                celery.wait(timeout=15)
            except subprocess.TimeoutExpired:
                celery.kill()

    def _wait_for_db_and_migrate(self):
        self.stdout.write(self.style.NOTICE('Waiting for database...'))
        for attempt in range(1, 31):
            try:
                connection.ensure_connection()
                break
            except OperationalError:
                if attempt == 30:
                    self.stderr.write(self.style.ERROR('Database not reachable after 30 attempts.'))
                    sys.exit(1)
                self.stdout.write(f'  attempt {attempt}/30 — retrying in 2s')
                time.sleep(2)

        self.stdout.write(self.style.NOTICE('Running migrations...'))
        call_command('migrate', interactive=False, verbosity=1)

    def _maybe_create_superuser(self):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL') or os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        if not email or not password:
            return

        os.environ.setdefault('DJANGO_SUPERUSER_EMAIL', email)
        self.stdout.write(self.style.NOTICE('Ensuring superuser exists...'))
        try:
            call_command('createsuperuser', interactive=False, verbosity=0)
        except Exception:
            # User already exists or other non-fatal create error
            pass
