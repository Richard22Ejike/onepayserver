from django.urls import path
from . import views

urlpatterns = [
    path('transaction/make-bill-payment/<str:pk>/', views.makeBillPayment),
    path('transaction/make-external-transfer/<str:pk>/', views.makeExternalTransfer),
    path('transaction/make-internal-transfer/<str:pk>/', views.makeInternelTransfer),
    path('transaction/fund-account-with-card/<str:pk>/', views.fundAccountWithCard),
    path('transaction/issue-card/', views.IssueCard),
    path('transaction/get-cards/<str:pk>/', views.getCards),
    path('transaction/add-card/', views.SaveCard),
    path('transaction/get-transactions/<str:pk>/', views.getTransactions),
    path('transaction/change-pin/<str:pk>/', views.ChangePin),
    path('transaction/issue-card/', views.IssueCard),
    path('transaction/save-card/', views.SaveCard),
    path('transaction/details-card/<str:pk>/', views.getCardDetails),
    path('transaction/link-card/<str:pk>/', views.linkCard),
    path('transaction/withdraw-card/<str:pk>/', views.WithDrawCard),
    path('transaction/create-escrow/<str:pk>/', views.CreateEscrow),
    path('transaction/edit-escrow/<str:pk>/', views.EditEscrow),
    path('transaction/get-escrows/<str:pk>/', views.getEscrows),
    path('transaction/create-payment-link/', views.CreatePaymentLink),
    path('transaction/get-payment-links/<str:pk>/', views.getPaymentLinks),
    path('transaction/edit-payment-link/<str:pk>/', views.EditPaymentLink),
]