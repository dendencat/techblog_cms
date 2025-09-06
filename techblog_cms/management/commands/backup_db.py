"""
Database backup management command
"""
import os
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection


class Command(BaseCommand):
    help = 'Create a backup of the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Output file path for the backup'
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Compress the backup with gzip'
        )

    def handle(self, *args, **options):
        db_settings = connection.settings_dict
        
        # Generate backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        if options['output']:
            backup_file = options['output']
        else:
            backup_file = os.path.join(
                backup_dir,
                f"backup_{db_settings['NAME']}_{timestamp}.sql"
            )
        
        # Build pg_dump command
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']
        
        cmd = [
            'pg_dump',
            '-h', db_settings['HOST'],
            '-p', str(db_settings['PORT']),
            '-U', db_settings['USER'],
            '-d', db_settings['NAME'],
            '--no-password',
            '--verbose',
        ]
        
        try:
            self.stdout.write(f"Creating backup: {backup_file}")
            
            if options['compress']:
                backup_file += '.gz'
                with open(backup_file, 'wb') as f:
                    p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env)
                    p2 = subprocess.Popen(['gzip'], stdin=p1.stdout, stdout=f)
                    p1.stdout.close()
                    p2.communicate()
            else:
                with open(backup_file, 'w') as f:
                    subprocess.run(cmd, stdout=f, env=env, check=True)
            
            self.stdout.write(
                self.style.SUCCESS(f"Successfully created backup: {backup_file}")
            )
            
            # Get file size
            size = os.path.getsize(backup_file)
            size_mb = size / (1024 * 1024)
            self.stdout.write(f"Backup size: {size_mb:.2f} MB")
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f"Backup failed: {e}")
            )
            raise
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Unexpected error: {e}")
            )
            raise