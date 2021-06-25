import tempfile

from PIL import Image
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from . import models


def temporary_image():
    image = Image.new('RGB', (1000, 1000))

    tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
    image.save(tmp_file)
    tmp_file.seek(0)
    return tmp_file


class ImageProductTests(APITestCase):
    def setUp(self) -> None:
        self.user = models.User.objects.create_user(username="test", email="test@example.com",
                                                    password="TestPassword123")
        self.client.login(username="test", password="TestPassword123")
        plan = models.Plan.objects.create(name="Basic")
        models.PlanThumbnailSetting.objects.create(thumbnail_size=200, plan=plan)
        self.user.user_tier.plan = plan

    def test_create_image_product(self):
        self.client.force_authenticate(self.user)
        url = reverse("image-list")
        temp_image = temporary_image()
        data = {"image": temp_image}
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(models.ImageProduct.objects.count(), 1)
