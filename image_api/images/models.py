import mimetypes
import uuid

from annoying.fields import AutoOneToOneField
from django.contrib.auth.models import AbstractUser
from django.core.validators import validate_image_file_extension, FileExtensionValidator
from django.db import models
from sorl.thumbnail import ImageField, delete

from . import validators


def upload_to(instance, filename):
    return f"images/{instance.owner.username}/{filename}"


def get_default_plan():
    return Plan.objects.get_or_create(name="Basic")[0].id


class User(AbstractUser):
    pass


class Tier(models.Model):
    user = AutoOneToOneField("User", on_delete=models.CASCADE, related_name="user_tier")
    plan = models.ForeignKey("Plan", on_delete=models.CASCADE, default=get_default_plan)

    def __str__(self):
        return f"{self.user.username}: {self.plan}"


class ImageProduct(models.Model):
    _allowed_extensions = ["jpg", 'png']

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4(), editable=False)
    owner = models.ForeignKey("User", on_delete=models.CASCADE, related_name="user_images")
    image = ImageField(upload_to=upload_to,
                       validators=[validate_image_file_extension, FileExtensionValidator(_allowed_extensions)])
    mimetype = models.CharField(max_length=20, default="image/jpeg")

    def delete(self, using=None, keep_parents=False):
        delete(self.image)
        super().delete()

    def save(self, *args, **kwargs):
        mimetypes.init()
        self.mimetype = mimetypes.guess_type(str(self.image))[0]
        super(ImageProduct, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.image.name)


class Plan(models.Model):
    name = models.TextField(max_length=20)
    link_to_original = models.BooleanField(default=False)
    expiring_link = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class PlanThumbnailSetting(models.Model):
    plan = models.ForeignKey("Plan", on_delete=models.CASCADE, related_name="thumbnail_settings")
    thumbnail_size = models.IntegerField()

    def __str__(self):
        return f"{self.plan.name}: {self.thumbnail_size}px"


class ExpiringToken(models.Model):
    token = models.CharField(max_length=255, primary_key=True)
    duration = models.IntegerField(validators=[validators.validate_duration_value])
    identifier = models.CharField(max_length=10)
    image = models.ForeignKey("ImageProduct", on_delete=models.CASCADE, related_name="image_expiring_token",
                              db_column="imageproduct_uuid")

    def __str__(self):
        return f"{self.image.name}: {self.token}"
