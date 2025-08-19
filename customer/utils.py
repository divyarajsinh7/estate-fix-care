from .models import *

def create_booking_notifications(user_profile, electrician_profile, booking):
    """
    Creates booking notifications for both the customer and the electrician,
    and includes related party info.
    Returns: (user_notification, electrician_notification) as dicts.
    """
    # For the customer
    user_notification = Notification.objects.create(
        user=user_profile,
        electrician=electrician_profile,
        recipient_type='user',
        title='Booking Confirmed',
        message=f"Your booking for '{booking.service.name}' has been confirmed. OTP: {booking.service_start_otp}",
        type='booking',
        channel='app',
        is_sent=True
        
    )

    # For the electrician
    electrician_notification = Notification.objects.create(
        electrician=electrician_profile,
        user=user_profile,
        recipient_type='electrician',
        title='Service Booked For You',
        message=f"You have been assigned a service for '{booking.service.name}'",
        type='booking',
        channel='app',
        is_sent=True
    )

    # Return serialized versions
    return {
        "user_notification": {
            "id": user_notification.id,
            "title": user_notification.title,
            "message": user_notification.message
        },
        "electrician_notification": {
            "id": electrician_notification.id,
            "title": electrician_notification.title,
            "message": electrician_notification.message
        }
    }


# def find_matching_electrician(self, service_name, address, km_limit):
#     electricians = CustomerProfile.objects.filter(role='electrician')

#     service_keywords = [word.strip().lower() for word in service_name.split() if word.strip()]

#     for electrician in electricians:
#         if electrician.service_skill:
#             skill_keywords = []
#             for skill_phrase in electrician.service_skill.split(','):
#                 skill_keywords.extend(skill_phrase.strip().lower().split())

#             if any(word in skill_keywords for word in service_keywords):
#                 if electrician.latitude and electrician.longitude:
#                     distance = self.get_distance(
#                         (address.latitude, address.longitude),
#                         (electrician.latitude, electrician.longitude)
#                     )
#                     if distance <= km_limit:
#                         return electrician
#     return None

# def get_distance(self, origin, destination):
#     """
#     Uses Google Maps Distance Matrix API to get distance in km
#     """
#     import requests
#     import math
#     from django.conf import settings

#     api_key = settings.GOOGLE_MAPS_API_KEY
#     url = f"https://maps.googleapis.com/maps/api/distancematrix/json"
#     params = {
#         "origins": f"{origin[0]},{origin[1]}",
#         "destinations": f"{destination[0]},{destination[1]}",
#         "key": api_key
#     }
#     response = requests.get(url, params=params).json()
#     try:
#         meters = response["rows"][0]["elements"][0]["distance"]["value"]
#         return meters / 1000  # in km
#     except:
#         return math.inf