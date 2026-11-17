import secrets
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from authentication.models import Profile, RoleChoices, TechChoices


class Command(BaseCommand):
    help = "Create 15 sample profiles and save their generated credentials locally."

    def handle(self, *args, **options):
        groups = (
            ("coordinator", "Project Coordinator", RoleChoices.COORDINATOR, None),
            ("backend", "Backend Developer", RoleChoices.DEVELOPER, TechChoices.BACKEND),
            ("frontend", "Frontend Developer", RoleChoices.DEVELOPER, TechChoices.FRONTEND),
            ("fullstack", "Fullstack Developer", RoleChoices.DEVELOPER, TechChoices.FULLSTACK),
            ("uiux", "UI/UX Designer", RoleChoices.DEVELOPER, TechChoices.UI_UX),
        )
        profiles = [
            (f"{prefix}{number:02}", title, role, tech)
            for prefix, title, role, tech in groups
            for number in range(1, 4)
        ]
        credentials_path = Path(__file__).resolve().parents[2] / "credentials.txt"

        if credentials_path.exists():
            raise CommandError(
                f"{credentials_path} already exists; move it before generating new credentials."
            )

        usernames = [username for username, *_ in profiles]
        existing = list(Profile.objects.filter(username__in=usernames).values_list("username", flat=True))
        if existing:
            raise CommandError(
                "Sample usernames already exist: " + ", ".join(sorted(existing))
            )

        credentials = []
        with transaction.atomic():
            for username, title, role, tech in profiles:
                password = secrets.token_urlsafe(24)
                Profile.objects.create_user(
                    username=username,
                    password=password,
                    first_name=f"{title} {username[-2:]}",
                    email=f"{username}@example.com",
                    role=role,
                    tech=tech,
                )
                credentials.append(
                    f"Role: {title}\nUsername: {username}\nPassword: {password}\n"
                )

            try:
                credentials_path.write_text(
                    "Development sample accounts — change these passwords before use elsewhere.\n\n"
                    + "\n".join(credentials),
                    encoding="utf-8",
                )
            except OSError as exc:
                raise CommandError(
                    f"Profiles were not saved because credentials could not be written to "
                    f"{credentials_path}: {exc}"
                ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(profiles)} profiles. Credentials saved to {credentials_path}."
            )
        )
