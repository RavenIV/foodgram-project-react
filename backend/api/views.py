from djoser.permissions import CurrentUserOrAdmin
from djoser.views import UserViewSet
from rest_framework.decorators import action


class CustomUserViewSet(UserViewSet):

    @action(["get"], detail=False, permission_classes=[CurrentUserOrAdmin])
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        if request.method == "GET":
            return self.retrieve(request, *args, **kwargs)
