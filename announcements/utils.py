# announcements/utils.py
import logging
from django.core.mail import send_mail
from django.conf import settings
from .models import Announcement, Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

def notify_user_rejection(announcement):
    try:
        if not hasattr(announcement, 'owner') or announcement.owner is None:
            logger.error(f"Announcement #{announcement.id} has no owner")
            return

        message = f'Ваше оголошення "{announcement.title}" не було схвалено адміністрацією. Причина: {announcement.admin_comment or "Не вказано."}'
        logger.debug(f"Creating notification for user {announcement.owner.username}: {message}")

        notification = Notification.objects.create(
            user=announcement.owner,
            message=message,
            related_announcement=announcement
        )
        logger.info(f"Notification created: ID={notification.id}, user={announcement.owner.username}")

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{announcement.owner.id}',
            {
                'type': 'notify',
                'message': message,
            }
        )
        logger.debug(f"Sent WebSocket notification to user {announcement.owner.id}")

        if announcement.owner.email:
            subject = f'Ваше оголошення "{announcement.title}" відхилено'
            email_message = f'Шановний {announcement.owner.username},\n\n{message}\n\nЗ повагою,\nКоманда vseOgolosha'
            send_mail(
                subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                [announcement.owner.email],
                fail_silently=False,
            )
            logger.info(f"Email sent to {announcement.owner.email} for announcement #{announcement.id}")
        else:
            logger.warning(f"User {announcement.owner.username} has no email address")

    except Exception as e:
        logger.error(f"Error in notify_user_rejection for announcement #{announcement.id}: {str(e)}")
        raise