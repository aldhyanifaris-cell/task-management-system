"""
Custom Management Commands
===========================
seed_data.py - Populates database with sample data for development.
"""

import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from tasks.models import Task, Category

User = get_user_model()


class Command(BaseCommand):
    """Management command to seed the database with sample data."""

    help = 'Seed the database with sample data for development/testing'

    def add_arguments(self, parser) -> None:
        """Add command arguments."""
        parser.add_argument(
            '--users', type=int, default=3,
            help='Number of sample users to create (default: 3)'
        )
        parser.add_argument(
            '--tasks', type=int, default=20,
            help='Number of sample tasks to create (default: 20)'
        )
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear existing data before seeding'
        )

    def handle(self, *args, **options) -> None:
        """Execute the command."""
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Task.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('Data cleared.'))

        self.stdout.write('Seeding database...')

        # Create users
        users = self._create_users(options['users'])

        # Create categories
        categories = self._create_categories(users[0])

        # Create tasks
        self._create_tasks(users, categories, options['tasks'])

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded: {len(users)} users, '
                f'{len(categories)} categories, {options["tasks"]} tasks.'
            )
        )

    def _create_users(self, count: int) -> list:
        """Create sample users."""
        users = []
        for i in range(1, count + 1):
            user, created = User.objects.get_or_create(
                email=f'user{i}@example.com',
                defaults={
                    'username': f'user{i}',
                    'first_name': f'User{i}',
                    'last_name': 'Sample',
                    'bio': f'Sample bio for user {i}',
                }
            )
            if created:
                user.set_password('SamplePass123!')
                user.save()
                self.stdout.write(f'  Created user: {user.email}')
            users.append(user)
        return users

    def _create_categories(self, owner) -> list:
        """Create sample categories."""
        categories_data = [
            {'name': 'Work', 'color': '#007bff', 'icon': 'briefcase'},
            {'name': 'Personal', 'color': '#28a745', 'icon': 'user'},
            {'name': 'Shopping', 'color': '#fd7e14', 'icon': 'shopping-cart'},
            {'name': 'Health', 'color': '#dc3545', 'icon': 'heart'},
            {'name': 'Learning', 'color': '#6f42c1', 'icon': 'book'},
        ]

        categories = []
        for data in categories_data:
            cat, _ = Category.objects.get_or_create(
                name=data['name'],
                defaults={**data, 'created_by': owner}
            )
            categories.append(cat)
            self.stdout.write(f'  Created category: {cat.name}')
        return categories

    def _create_tasks(self, users: list, categories: list, count: int) -> None:
        """Create sample tasks."""
        statuses = [s[0] for s in Task.Status.choices]
        priorities = [p[0] for p in Task.Priority.choices]

        sample_titles = [
            'Review project proposal', 'Fix login bug', 'Write unit tests',
            'Update documentation', 'Deploy to staging', 'Code review',
            'Team meeting preparation', 'Buy groceries', 'Exercise routine',
            'Read Python book', 'Setup CI/CD pipeline', 'Database optimization',
            'API integration', 'UI redesign', 'Performance testing',
            'Security audit', 'Refactor authentication', 'Add search feature',
            'Create dashboard', 'Write blog post', 'Email responses',
            'Budget planning', 'Quarterly report', 'Team retrospective'
        ]

        for i in range(count):
            due = timezone.now() + timedelta(days=random.randint(-5, 30))
            Task.objects.create(
                title=random.choice(sample_titles) + f' #{i+1}',
                description=f'Sample description for task {i+1}. '
                            f'This is auto-generated content.',
                status=random.choice(statuses),
                priority=random.choice(priorities),
                owner=random.choice(users),
                category=random.choice(categories + [None]),
                due_date=due if random.random() > 0.3 else None,
                tags=random.choice(['backend,api', 'frontend', 'devops', 'design', ''])
            )
