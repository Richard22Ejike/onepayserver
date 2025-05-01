import uuid

import requests
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import F, FloatField
from django.db.models.functions import Cast, Sqrt, Power
from math import radians
from nearme.models import NearMeProduct, ChatNearMeRoom
from nearme.serializers import NearMeProductSerializer, ChatNearMeRoomSerializer
from transactions.models import ChatMessage
from transactions.serializers import ChatSerializer
from users.models import User


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_Near_Me_admin_Products(request):
    near_me_products = NearMeProduct.objects.all()
    serializer = NearMeProductSerializer(near_me_products, many=True)
    print(serializer.data)
    return Response(serializer.data)


@permission_classes([IsAuthenticated])
@api_view(['POST'])
def CreateNearMeProduct(request, pk):
    try:
        data = request.data
        # Generate a unique reference number using a combination of timestamp and UUID
        reference = f"{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

        # Create the escrow
        near_me_product = NearMeProduct.objects.create(
            product_id=data.get('product_id', reference),  # Use the generated reference if not provided
            seller_name=data.get('seller_name', reference),
            seller_image=data.get('seller_image', reference),
            seller_phone_number=data.get('seller_phone_number', reference),
            product_category=data.get('product_category', ''),
            product_name=data.get('product_name', ''),
            product_images=data.get('product_images', []),
            customer_id=data.get('customer_id', ''),
            video=data.get('video', ''),
            title=data.get('title', ''),
            location=data.get('location', ''),
            lat=data.get('lat', ''),
            long=data.get('long', ''),
            brand=data.get('brand', ''),
            type=data.get('type', ''),
            condition=data.get('condition', ''),
            description=data.get('description', ''),
            price=data.get('price', ''),
            delivery=data.get('delivery', ''),
            status=data.get('status', 'Pending'),  # Default status
            seller_email=data.get('seller_email', 'email@mail.com'),
            seller_id=data.get('seller_id', '148')

        )

        serializer = NearMeProductSerializer(near_me_product, many=False)
        print(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except requests.exceptions.RequestException as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        print(e)
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@permission_classes([IsAuthenticated])
@api_view(['PUT', 'PATCH'])
def edit_near_me_product(request, pk):
    try:
        # Retrieve the product by primary key
        near_me_product = NearMeProduct.objects.get(pk=pk)

        if request.data.get("status") == 'Delete':
            near_me_product.delete()
            return Response(
                {"message": "Product deleted successfully."},
                status=status.HTTP_200_OK
            )
        # Update the product with the provided data
        serializer = NearMeProductSerializer(
            near_me_product, data=request.data, partial=True
        )

        # Check if the data is valid
        if serializer.is_valid():
            serializer.save()  # Save the updated instance
            print(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            # If validation fails, return errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except NearMeProduct.DoesNotExist:
        # If the product does not exist, return an error
        return Response(
            {"error": "NearMeProduct not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        # Catch all other exceptions and return their details
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_filtered_products(request):
    try:
        # Retrieve query parameters
        location = request.query_params.get('location', None)  # State
        lat = request.query_params.get('lat', None)  # Latitude
        long = request.query_params.get('long', None)  # Longitude
        name = request.query_params.get('name', None)  # Product name

        if not lat or not long:
            return Response({"error": "Latitude and longitude are required for sorting."},
                            status=status.HTTP_400_BAD_REQUEST)

        lat = float(lat)
        long = float(long)

        # Base queryset
        products = NearMeProduct.objects.all()
        serializer = NearMeProductSerializer(products, many=True)
        print(f'the first one {serializer.data}')

        # # Filter by location (state) if provided
        # if location:
        #     products = products.filter(location__iexact=location)
        #
        # Filter by product name
        # if name != '':
        #     if name:
        #         products = products.filter(
        #             Q(product_name__icontains=name) | Q(product_category__icontains=name)
        #         )

        # Add distance annotation to sort by proximity
        products = products.annotate(
            lat_float=Cast('lat', FloatField()),
            long_float=Cast('long', FloatField()),
            distance=Sqrt(
                Power(F('lat_float') - lat, 2) + Power(F('long_float') - long, 2)
            )
        ).order_by('distance')  # Sort by distance in ascending order

        # Serialize the sorted results
        serializer = NearMeProductSerializer(products, many=True)
        print(f'the second one {serializer.data}')
        return Response(serializer.data, status=status.HTTP_200_OK)

    except ValueError:
        # Handle invalid latitude/longitude input
        return Response({"error": "Invalid latitude or longitude values"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # Catch all other exceptions and return their details
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_chat_ids(request, pk):
    try:
        print('got me')
        # Filter ChatNearMeRoom by `sender` or `receiver` user id
        chat_rooms = ChatNearMeRoom.objects.filter(
            sender_id=pk
        ) | ChatNearMeRoom.objects.filter(receiver_id=pk)

        serializer = ChatNearMeRoomSerializer(chat_rooms, many=True)
        print(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f'Error: {e}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@permission_classes([IsAuthenticated])
@api_view(['POST'])
def create_or_get_chatroom(request):
    """
    Check if a chat room exists by chat_id.
    If it doesn't, create a new chat room and return it.
    If it exists, update the sender_image and return the chat room.
    """
    chat_id = request.data.get('chat_id')
    sender_id = request.data.get('sender_id')
    receiver_id = request.data.get('receiver_id')

    if not chat_id or not sender_id or not receiver_id:
        return Response(
            {"error": "chat_id, sender_id, and receiver_id are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if a chat room with the given chat_id exists
    chat_room = ChatNearMeRoom.objects.filter(chat_id=chat_id).first()

    if chat_room:
        # If the room exists, update the sender_image if provided
        sender_image = request.data.get('sender_image')

        if sender_image:
            chat_room.sender_image = sender_image
            chat_room.save()

        # Return the updated chat room
        serializer = ChatNearMeRoomSerializer(chat_room)
        return Response(serializer.data, status=status.HTTP_200_OK)

    try:
        # Get sender and receiver objects
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)

        # Create a new chat room
        chat_room = ChatNearMeRoom.objects.create(
            chat_id=chat_id,
            sender=sender,
            receiver=receiver,
            sender_image=request.data.get('sender_image'),
            sender_name=request.data.get('sender_name'),
            last_message="",  # Default to empty if no messages yet
        )

        # Serialize the created room
        serializer = ChatNearMeRoomSerializer(chat_room)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except User.DoesNotExist:
        return Response(
            {"error": "Sender or receiver user not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {"error": f"An unexpected error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def getNearMeProducts(request, pk):
    print('friends')
    nearmeproducts = NearMeProduct.objects.filter(customer_id=pk)
    serializer = NearMeProductSerializer(nearmeproducts, many=True)
    print(serializer.data)
    return Response(serializer.data)


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def getChats(request, pk):
    messages = ChatMessage.objects.filter(chat_id=pk)
    serializer = ChatSerializer(messages, many=True)
    print(serializer.data)
    return Response(serializer.data)
