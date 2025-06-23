import uuid

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
# from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password
from django.utils.timezone import now as djnow

# Create your models here.

class AccountManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        pass

    def create_superuser(self, email, password=None, **extra_fields):
        pass

class User(AbstractBaseUser, PermissionsMixin):
    uuid = models.UUIDField(default=uuid.uuid4(), max_length=64, unique=True)

    full_name = models.CharField(max_length=50, null=True)
    avatar = models.ImageField(upload_to='avatars', null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    updated_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_updated_by")
    created_at = models.DateTimeField(editable=False, default=djnow)

    objects = AccountManager()
    USERNAME_FIELD = 'uuid'

    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(fields=['uuid'], name='unique_uuid', condition=models.Q(is_deleted=False)),
    #     ]

class Account(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="%(class)s_user")
    
    username = models.CharField(max_length=255)
    password = models.CharField(_("password"), max_length=128)

    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )

    is_deleted = models.BooleanField(default=False)
    updated_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_updated_by")
    created_at = models.DateTimeField(editable=False, default=djnow)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['username'], name='unique_username', condition=models.Q(is_deleted=False)),
        ]

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)


class AbstractBaseModel(models.Model):
    created_at = models.DateTimeField(editable=False, default=djnow)
    created_by = models.ForeignKey(Account, on_delete=models.DO_NOTHING, null=True, blank=True, related_name="%(class)s_created_by")

    updated_at = models.DateTimeField(auto_created=True, auto_now=True)
    updated_by = models.ForeignKey(Account, on_delete=models.DO_NOTHING, null=True, blank=True, related_name="%(class)s_updated_by")

    is_deleted = models.BooleanField(verbose_name="Trạng thái xoá", default=False, help_text="Trạng thái xoá")

    class Meta:
        abstract = True
