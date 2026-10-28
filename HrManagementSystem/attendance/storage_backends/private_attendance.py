from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateAttendanceStorage(FileSystemStorage):
    """
    Attendance photos stored outside public MEDIA_ROOT.
    Photos must only be served through an authenticated,
    permission-checked Django view.
    """

    def __init__(self, *args, **kwargs):
        kwargs["location"] = str(settings.ATTENDANCE_PRIVATE_ROOT)
        kwargs["base_url"] = None
        super().__init__(*args, **kwargs)

    def url(self, name):
        raise NotImplementedError(
            "Private attendance photos cannot have public URLs."
        )
