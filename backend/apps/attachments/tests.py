from unittest.mock import Mock

from botocore.exceptions import ClientError
from django.http import Http404
from django.test import SimpleTestCase

from .views import attachment_file_response


class AttachmentFileResponseTests(SimpleTestCase):
    def _attachment_raising(self, exc):
        attachment = Mock()
        attachment.filename = "report.pdf"
        attachment.file.open.side_effect = exc
        return attachment

    def _s3_error(self, code):
        return ClientError({"Error": {"Code": code}}, "HeadObject")

    def test_missing_local_file_returns_not_found(self):
        attachment = self._attachment_raising(FileNotFoundError())

        with self.assertRaisesMessage(Http404, "Attachment file not found"):
            attachment_file_response(attachment)

    def test_missing_or_forbidden_s3_file_returns_not_found(self):
        for code in ("403", "404", "AccessDenied", "Forbidden", "NoSuchKey", "NotFound"):
            with self.subTest(code=code):
                attachment = self._attachment_raising(self._s3_error(code))

                with self.assertRaisesMessage(Http404, "Attachment file not found"):
                    attachment_file_response(attachment)

    def test_unexpected_s3_error_still_propagates(self):
        attachment = self._attachment_raising(self._s3_error("InternalError"))

        with self.assertRaises(ClientError):
            attachment_file_response(attachment)
