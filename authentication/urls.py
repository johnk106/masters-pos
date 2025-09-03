from django.urls import path
from . import views


app_name = "authentication"
urlpatterns = [
    path('users/',views.users,name='users'),
    path('roles/',views.roles,name='roles'),
    path('profile/',views.profile,name='profile'),
    path("users/create/", views.create_user_view, name="create-user"),
    path("users/<int:user_id>/edit/", views.edit_user_view, name="edit-user"),
    path("users/<int:user_id>/delete/", views.delete_user_view, name="delete-user"),
    path("roles/create/", views.create_role_view, name="create-role"),
    path("roles/<int:role_id>/edit/", views.edit_role_view, name="edit-role"),
    path("roles/<int:role_id>/delete/", views.delete_role_view, name="delete-role"),
    path("roles/<int:role_id>/permissions/", views.manage_permissions_view, name="manage-permissions"),
    path("accounts/login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]


