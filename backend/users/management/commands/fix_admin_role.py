from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = 'Set admin role for superusers who don\'t have a role'

    def handle(self, *args, **options):
        superusers = User.objects.filter(is_superuser=True)
        
        updated_count = 0
        for user in superusers:
            if not user.role:
                user.role = 'admin'
                user.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Updated {user.email} with role "admin"')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'{user.email} already has role "{user.role}"')
                )
        
        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully updated {updated_count} admin user(s)')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\nNo admin users needed role updates')
            )
