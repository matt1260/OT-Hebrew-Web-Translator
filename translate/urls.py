from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import include

from . import views

urlpatterns = [
    path('', views.translate, name='translate'),
    path('edit/', views.edit, name='edit'),
    path('RBT/edit/', views.edit, name='edit'),
    path('translate/', views.translate, name='translate'),
    path('RBT/translate/', views.translate, name='rbt_translate'),
    path('find_replace/', views.find_replace_view, name='find_replace'),
    path('undo_replacements/', views.undo_replacements_view, name='undo_replacements'),
    path('search_footnotes/', views.search_footnotes, name='search_footnotes'),
    path('edit_footnote/', views.edit_footnote, name='edit_footnote'),
    path('RBT/edit_footnote/', views.edit_footnote, name='edit_footnote'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('RBT/edit_search/', views.edit_search, name='edit_search'),

]