def user_permissions(request):
    if request.user.is_authenticated:
        permissions = request.user.get_permissions_set()
    else:
        permissions = set()
    return {'user_permissions': permissions}