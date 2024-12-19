from django.urls import path
from nearme import views

urlpatterns = [
    # Near Me Product APIs
    path('near-me/create-product/<str:pk>/', views.CreateNearMeProduct, name='create_near_me_product'),
    path('near-me/edit-product/<str:pk>/', views.edit_near_me_product, name='edit_near_me_product'),
    path('near-me/get-product/<str:pk>/', views.getNearMeProducts, name='get_near_me_products'),
    path('near-me/get-filtered-products/', views.get_filtered_products, name='get_filtered_products'),

    # Chat Room APIs
    path('near-me/chat-rooms/<str:pk>/', views.get_chat_ids, name='get_chat_ids'),
    path('near-me/get_chat/<str:pk>/', views.getChats, name='get_chat'),
    path('near-me/create-chat-room/', views.create_or_get_chatroom, name='create_or_get_chatroom'),
]
