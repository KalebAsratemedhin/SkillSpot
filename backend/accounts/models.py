import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Super user must have the is_superuser field true")

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    class UserType(models.TextChoices):
        CLIENT = 'CLIENT'
        PROVIDER = 'PROVIDER'
        BOTH = 'BOTH'


    id = models.UUIDField(
            primary_key=True,
            default=uuid.uuid4,
            editable=False,
            help_text=("Unique identifier required for the user")
    )

    email = models.EmailField(
            unique=True,
            help_text="A valid email is required."
    )

    username = None

    REQUIRED_FIELDS = []

    user_type = models.CharField(
            max_length=10,
            choices=UserType.choices,
            default=UserType.CLIENT,
            help_text="Type of user is required"
    )

    USERNAME_FIELD = 'email'


    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        db_table = 'accounts_user'


    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower().strip()
        super().save(*args, **kwargs)






