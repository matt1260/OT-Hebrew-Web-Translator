from django.urls import path

from . import views

urlpatterns = [
    path('', views.search, name='search'),
    path('search/', views.search, name='search'),
    path('paraphrase/', views.paraphrase, name='paraphrase'),
    path('RBT/paraphrase/', views.paraphrase, name='paraphrase'),
    path('RBT/search/word/', views.word_view, name='word'),
]