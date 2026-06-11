from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Resource
from .pdf_utils import build_simple_pdf


def build_simple_docx():
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>Volunteer checklist</w:t></w:r></w:p></w:body>"
        "</w:document>"
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


class ResourceApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="volunteer", password="test-password")
        self.checklist = Resource.objects.create(
            title="Beach Event Checklist",
            description="Packing and safety list",
            category=Resource.Category.CHECKLIST,
            pdf_file=SimpleUploadedFile("checklist.pdf", build_simple_pdf("Checklist", "Test PDF"), content_type="application/pdf"),
        )
        self.educational = Resource.objects.create(
            title="Tsunami Education Guide",
            description="Learning material for students",
            category=Resource.Category.EDUCATIONAL,
            pdf_file=SimpleUploadedFile("guide.pdf", build_simple_pdf("Guide", "Test PDF"), content_type="application/pdf"),
        )
        Resource.objects.create(
            title="Hidden Draft",
            category=Resource.Category.CHECKLIST,
            is_active=False,
            pdf_file=SimpleUploadedFile("draft.pdf", build_simple_pdf("Draft", "Test PDF"), content_type="application/pdf"),
        )

    def test_anonymous_users_cannot_list_resources(self):
        response = self.client.get(reverse("api-resource-list"))

        self.assertEqual(response.status_code, 401)

    def test_logged_in_users_can_list_active_resources(self):
        self.client.login(username="volunteer", password="test-password")

        response = self.client.get(reverse("api-resource-list"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["resources"]), 2)

    def test_search_and_category_filters_resources(self):
        self.client.login(username="volunteer", password="test-password")

        response = self.client.get(reverse("api-resource-list"), {"search": "tsunami", "category": "educational"})

        self.assertEqual(response.status_code, 200)
        resources = response.json()["resources"]
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]["title"], "Tsunami Education Guide")

    def test_download_serves_active_pdf(self):
        self.client.login(username="volunteer", password="test-password")

        response = self.client.get(reverse("api-resource-download", args=[self.checklist.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_download_serves_active_docx(self):
        docx = Resource.objects.create(
            title="Editable Volunteer Checklist",
            description="Word document version",
            category=Resource.Category.CHECKLIST,
            pdf_file=SimpleUploadedFile(
                "editable-checklist.docx",
                build_simple_docx(),
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        )
        self.client.login(username="volunteer", password="test-password")

        response = self.client.get(reverse("api-resource-download", args=[docx.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.assertIn("editable-checklist.docx", response["Content-Disposition"])

    def test_download_rejects_missing_resource(self):
        self.client.login(username="volunteer", password="test-password")

        response = self.client.get(reverse("api-resource-download", args=[9999]))

        self.assertEqual(response.status_code, 404)

    def test_pdf_upload_must_have_pdf_signature(self):
        resource = Resource(
            title="Bad PDF",
            category=Resource.Category.CHECKLIST,
            pdf_file=SimpleUploadedFile("bad.pdf", b"not a pdf", content_type="application/pdf"),
        )

        with self.assertRaises(ValidationError):
            resource.full_clean()

    def test_docx_upload_must_be_valid_docx_zip(self):
        resource = Resource(
            title="Bad DOCX",
            category=Resource.Category.CHECKLIST,
            pdf_file=SimpleUploadedFile("bad.docx", b"not a docx", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        )

        with self.assertRaises(ValidationError):
            resource.full_clean()
