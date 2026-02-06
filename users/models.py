from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    is_airport_admin = models.BooleanField(default=False)

    @property
    def is_admin(self):
        return self.is_staff or self.is_airport_admin
