from django.utils import timezone


def year(request):
    yearnow = timezone.now().year
    return {"year": yearnow}
