from django.core import signing
from django.http import HttpResponse, HttpResponseRedirect
from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from sorl.thumbnail import get_thumbnail

from . import models
from . import permissions
from . import serializers


@api_view(["GET"])
def api_root(request, format=None):
    return Response({
        "users": reverse("user-list", request=request, format=format),
        "images": reverse("image-list", request=request, format=format),
    })


class ImageList(generics.ListCreateAPIView):
    """
    Lists user's images
    """
    queryset = models.ImageProduct.objects.all()
    serializer_class = serializers.ImageProductSerializer
    permission_classes = (permissions.IsImageOwner,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = serializers.ImageProductSerializer(queryset, context={"request": self.request}, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return models.ImageProduct.objects.all()
        return models.ImageProduct.objects.filter(owner=user)


class ImageDetails(APIView):
    """
    Lists links to thumbnails and original details
    """
    permission_classes = (permissions.IsImageOwner,)

    def get_obj(self, pk):
        try:
            obj = models.ImageProduct.objects.get(pk=pk)
        except models.ImageProduct.DoesNotExist:
            return
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, pk):
        image = self.get_obj(pk)
        if not image:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if image.owner == request.user or request.user.is_staff or request.user.is_superuser:
            serializer = serializers.ImageDetailsSerializer(image, context={"request": request})
            return Response(serializer.data)
        return Response(status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, pk):
        image = self.get_obj(pk)
        if not image:
            return Response(status=status.HTTP_404_NOT_FOUND)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LinkView(generics.RetrieveAPIView):
    """
    List links to given image or thumbnail, expiring link and expiring link generator - if applicable
    """
    queryset = models.ImageProduct.objects.all()
    serializer_class = serializers.LinkSerializer
    permission_classes = (permissions.AllowedSize, permissions.IsImageOwner)

    def retrieve(self, request, *args, **kwargs):
        image = models.ImageProduct.objects.get(pk=kwargs.get("pk"))
        serializer = serializers.LinkSerializer(image, context={"request": request})
        return Response(serializer.data)


class ExpiringLinkView(generics.CreateAPIView):
    """
    Expiring link generation view, after generation sends redirect response to image links list
    """
    queryset = models.ExpiringToken.objects.all()
    serializer_class = serializers.ExpiringTokenSerializer
    permission_classes = (permissions.CanGenerateExpiringLink,)

    def post(self, request, *args, **kwargs):
        try:
            image = models.ImageProduct.objects.get(pk=kwargs.get("pk"))
        except models.ImageProduct.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = serializers.ExpiringTokenSerializer(data=request.data,
                                                         context={"request": request, "image": image})
        if serializer.is_valid():
            serializer.save()
            url = request.path.replace("get-temporary", "link")
            return HttpResponseRedirect(url)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lists users
    """
    queryset = models.User.objects.get_queryset().order_by("id")
    serializer_class = serializers.UserSerializer


@api_view(["GET"])
def temporary_link_view(request):
    """
    Returns response with image for temporary link
    """
    token = request.query_params.get("token")
    if token:

        # Check if token passed in link exists
        try:
            expiring_token = models.ExpiringToken.objects.get(token=token)
        except models.ExpiringToken.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        signer = signing.TimestampSigner()

        # Check if token is expired, get size form token
        try:
            size = signer.unsign(token, max_age=expiring_token.duration)
        except signing.SignatureExpired:
            expiring_token.delete()
            return Response(status=status.HTTP_404_NOT_FOUND)

        image = expiring_token.image
        mimetype = image.mimetype

        # Return response with image or thumbnail, depends on size
        if size == "original":
            return HttpResponse(image.image, content_type=mimetype)
        image = get_thumbnail(image.image, f"x{size}")
        return HttpResponse(image.read(), content_type=mimetype)

    return Response(status=status.HTTP_404_NOT_FOUND)
