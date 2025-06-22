from django import template

register = template.Library()


@register.filter
def is_kaprodi(user):
    try:
        return (
            hasattr(user, "dosen")
            and user.dosen.jabatan.filter(nama="kaprodi").exists()
        )
    except Exception:
        return False


@register.filter
def is_wd1(user):
    try:
        return hasattr(user, "dosen") and user.dosen.jabatan.filter(nama="wd1").exists()
    except Exception:
        return False


@register.filter(name="get_item")
def get_item(dictionary, key):
    """
    Memungkinkan untuk mengakses item dictionary dengan variabel di dalam template.
    Contoh: {{ my_dict|get_item:my_variable }}
    """
    if hasattr(dictionary, "get"):
        return dictionary.get(key)
    return None


@register.filter
def mul(value, arg):
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return ""
