from django.urls import path, re_path
from . import views
from . import consumer

urlpatterns = [
    path('transaction/get-all-transactions/', views.getTransaction),
    path('transaction/make-bill-payment/<str:pk>/', views.makeBillPayment),
    path('transaction/verify-bill-payment/', views.verifyBillPayment),
    path('transaction/make-external-transfer/<str:pk>/', views.makeExternalTransfer),
    path('transaction/make-internal-transfer/<str:pk>/', views.makeInternalTransfer),
    path('transaction/fund-account-with-card/<str:pk>/', views.fundAccountWithCard),
    path('transaction/issue-card/', views.IssueCard),
    path('transaction/get-cards/<str:pk>/', views.getCards),
    path('transaction/add-card/', views.SaveCard),
    path('transaction/get-transactions/<str:pk>/', views.getTransactions),
    path('transaction/change-pin/<str:pk>/', views.ChangePin),
    path('transaction/issue-card/', views.IssueCard),
    path('transaction/save-card/', views.SaveCard),
    path('transaction/details-card/<str:pk>/', views.getCardDetails),
    path('transaction/withdraw-card/<str:pk>/', views.WithDrawCard),
    path('transaction/create-escrow/<str:pk>/', views.CreateEscrow),
    path('transaction/edit-escrow/<str:pk>/', views.EditEscrow),
    path('transaction/get-escrows/<str:pk>/', views.getEscrows),
    path('transaction/get-user-escrows/<str:pk>/', views.getUserEscrows),
    path('transaction/update-escrow/<str:pk>/', views.updateEscrows),
    path('transaction/get-all-escrow/', views.getEscrows),
    path('transaction/dispute-escrows/<str:pk>/', views.disputeEscrows),
    path('transaction/release-escrows-fund/<str:pk>/', views.ReleaseEscrowsFund),
    path('transaction/make-payment-escrows/<str:pk>/', views.MakePaymentEscrows),
    path('transaction/get-message/<str:pk>/', views.getChats),
    path('transaction/create-payment-link/', views.CreatePaymentLink),
    path('transaction/get-payment-links/<str:pk>/', views.getPaymentLinks),
    path('transaction/create-checkout/', views.CreateCheckout),
    path('transaction/get-payment-link/<str:pk>/', views.getPaymentLink),
    path('transaction/edit-payment-link/<str:pk>/', views.EditPaymentLink),
    path('transaction/user-notification/<str:pk>/', views.getNotifications),

]
