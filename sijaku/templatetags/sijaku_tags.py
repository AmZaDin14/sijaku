from django import template

register = template.Library()

@register.filter
def is_kaprodi(user):
    try:
        return hasattr(user, 'dosen') and user.dosen.jabatan.filter(nama='kaprodi').exists()
    except Exception:
        return False
