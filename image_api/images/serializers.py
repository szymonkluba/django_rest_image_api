from django.core import signing
from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import SignatureExpired
from django.db.models import Min
from rest_framework import serializers
from sorl.thumbnail import get_thumbnail

from . import models


def get_data(request):
    # Helper function for returning size of image from url
    return str(request.query_params.get("size", "original"))


class ImageProductSerializer(serializers.ModelSerializer):
    """
    Image serializer - images/
    Lists all images uploaded by logged in user with smallest thumbnail possible as per user's plan settings
    """
    image = serializers.ImageField(write_only=True)
    owner = serializers.ReadOnlyField(source="owner.username")
    thumbnail = serializers.SerializerMethodField("get_thumbnail")

    class Meta:
        model = models.ImageProduct
        fields = ["url", "uuid", "owner", "image", "thumbnail"]

    def get_thumbnail(self, obj):
        request = self.context.get("request")
        min_thumbnail = request.user.user_tier.plan.thumbnail_settings.aggregate(Min("thumbnail_size"))
        thumbnail = get_thumbnail(obj.image, f"x{min_thumbnail.get('thumbnail_size__min')}")
        return request.build_absolute_uri(thumbnail.url)


class ImageDetailsSerializer(serializers.ModelSerializer):
    """
    Image details serializer - images/<str:pk>
    Return image details and hyperlinks to views with thumbnail or original image links - depends on user's plan settings
    """
    class Meta:
        model = models.ImageProduct
        fields = ["url", "uuid", "links"]

    links = serializers.SerializerMethodField("get_links")

    def get_links(self, obj):
        links = {}
        request = self.context.get("request")
        plan_settings = request.user.user_tier.plan
        thumbnail_settings = plan_settings.thumbnail_settings.all()

        # Get links to thumbnails details
        for setting in thumbnail_settings:
            links[f"thumbnail_{setting.thumbnail_size}px"] = request.build_absolute_uri(
                request.path + f'/link?size={setting.thumbnail_size}')

        # Get links to original details
        if plan_settings.link_to_original:
            links["original"] = request.build_absolute_uri(request.path + "/link")

        return links


class TierSerializer(serializers.ModelSerializer):
    """
    User tier serializer - used in User serializer to return information about user's plan
    """
    plan = serializers.SerializerMethodField("get_plan")

    class Meta:
        model = models.Tier
        fields = ["plan"]

    def get_plan(self, obj):
        return obj.plan.name


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    User serializer - /users/
    """
    user_images = serializers.HyperlinkedRelatedField(many=True, view_name="imageproduct-detail",
                                                      queryset=models.ImageProduct.objects.all())
    user_tier = TierSerializer(read_only=True)

    class Meta:
        model = models.User
        fields = ["url", "username", "user_images", "user_tier"]


class LinkSerializer(serializers.ModelSerializer):
    """
    Link serializer - 'images/<str:pk>/link'
    In JSON returns:
        image_link: link to image or thumbnail
        expiring_link: expiring link to image or thumbnail if generated
        temp_link_generator: link to expiring link generation view if user is allowed to generate expiring links
    """
    image_link = serializers.SerializerMethodField("get_image", read_only=True)
    expiring_link = serializers.SerializerMethodField("get_expiring_link", read_only=True)
    temp_link_generator = serializers.SerializerMethodField("get_generator_link", read_only=True)

    class Meta:
        model = models.ImageProduct
        fields = ["url", "uuid", "image_link", "expiring_link", "temp_link_generator"]

    def get_image(self, obj):
        request = self.context.get("request")
        # Check if size is passed in URL
        size = request.query_params.get("size", None)

        if size:
            # Return link to thumbnail
            image = get_thumbnail(obj.image, f"x{size}")
            return request.build_absolute_uri(image.url)

        # Return link to original
        return request.build_absolute_uri(obj.image.url)

    def get_expiring_link(self, obj):
        request = self.context.get("request")
        # Size is stored as identifier
        identifier = get_data(request)
        expiring_token = self.get_token(obj, identifier)

        # Check if token exists and return link or None if doesn't exist
        if not expiring_token:
            return

        if request.is_secure():
            return f"https://{request.get_host()}/temp?token={expiring_token.token}"
        return f"http://{request.get_host()}/temp?token={expiring_token.token}"

    def get_generator_link(self, obj):
        # Get link to expiring link generation view if user can generate expiring links
        request = self.context.get("request")
        if request.user.user_tier.plan.expiring_link:
            return request.build_absolute_uri(request.path.replace("link", "get-temporary"))
        return

    @staticmethod
    def get_token(obj, identifier):
        signer = signing.TimestampSigner()
        # Get token with given identifier
        try:
            expiring_token = obj.image_expiring_token.get(identifier=identifier)
        except ObjectDoesNotExist:
            return False

        # Check if token is expired, if it is remove token
        try:
            signer.unsign(expiring_token.token, max_age=expiring_token.duration)
        except SignatureExpired:
            expiring_token.delete()
            return False

        return expiring_token

    def to_representation(self, instance):
        # Overridden to_representation function to exclude empty keys
        ret = super(LinkSerializer, self).to_representation(instance)
        if not ret["expiring_link"]:
            ret.pop("expiring_link")
        if not ret["temp_link_generator"]:
            ret.pop("temp_link_generator")
        return ret


class ExpiringTokenSerializer(serializers.ModelSerializer):
    """
    Expiring token generation serializer - images/<str:pk>/get-temporary

    Accepts "duration" value through POST request and generates expiring token for given image
    """
    class Meta:
        model = models.ExpiringToken
        fields = ["duration"]

    def create(self, validated_data):
        image = self.context.get("image")
        request = self.context.get("request")
        # Get image size from helper function and store it as identifier
        identifier = get_data(request)
        token_signer = signing.TimestampSigner()
        token = token_signer.sign(identifier)
        duration = validated_data.get("duration")

        # Check if token for given image exists, replace token or create new one
        expiring_token, created = models.ExpiringToken.objects.get_or_create(identifier=identifier, defaults={
            "token": token,
            "image": image,
            "duration": duration,

        })

        if not created:
            expiring_token.image = image
            expiring_token.token = token
            expiring_token.duration = duration
        return expiring_token
