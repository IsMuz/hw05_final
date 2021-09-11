from django.core.paginator import Paginator


def paginate(request, obj):
    """Paginator function"""
    p = Paginator(obj, 10)
    p_num = request.GET.get('page')
    p_obj = p.get_page(p_num)
    return p_obj
