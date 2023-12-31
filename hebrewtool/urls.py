"""hebrewtool URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views

from translate import views

urlpatterns = [
    path('', include('search.urls')),
    path('RBT/', include('search.urls')),
    path('translate/', include('translate.urls')),
    path('RBT/translate/', include('translate.urls')),
    path('RBT/paraphrase/', include('search.urls')),
    path('edit/', views.edit, name='edit'),
    path('RBT/edit/', views.edit, name='edit'),
    path('edit_footnote/', views.edit_footnote, name='edit_footnote'),
    path('RBT/edit_footnote/', views.edit_footnote, name='edit_footnote'),
    path('RBT/edit_search/', views.edit_search, name='edit_search'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('RBT/edit/accounts/', include('django.contrib.auth.urls')),
    path('edit/accounts/', include('django.contrib.auth.urls')),
    path('RBT/translate/accounts/', include('django.contrib.auth.urls')),

]