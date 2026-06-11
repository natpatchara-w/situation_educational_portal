import json
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from docx import Document

from .checklist_generator import extract_docx_text
from .models import ChecklistJob, OpenAISettings, Resource
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


def build_readable_docx(text="Volunteer checklist", include_heading=True):
    document = Document()
    if include_heading:
        document.add_heading("Event Concept Note", level=1)
    if text:
        document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
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
        self.assertIn("editable-checklist", response["Content-Disposition"])
        self.assertIn(".docx", response["Content-Disposition"])

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


class ChecklistGeneratorApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="volunteer", password="test-password")

    def test_anonymous_users_cannot_generate_checklist(self):
        response = self.client.post(reverse("api-checklist-generate"))

        self.assertEqual(response.status_code, 401)

    def test_logged_in_user_without_permission_cannot_create_checklist_job(self):
        self.client.login(username="volunteer", password="test-password")
        upload = SimpleUploadedFile(
            "concept-note.docx",
            build_readable_docx("Marimba workshop for village students."),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        response = self.client.post(reverse("api-checklist-job-create"), {"concept_note": upload})

        self.assertEqual(response.status_code, 403)

    def test_extract_docx_text_reads_paragraphs(self):
        upload = SimpleUploadedFile(
            "concept-note.docx",
            build_readable_docx("Marimba workshop for village students."),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        text = extract_docx_text(upload)

        self.assertIn("Event Concept Note", text)
        self.assertIn("Marimba workshop", text)

    def test_generate_checklist_returns_pdf(self):
        self.client.login(username="volunteer", password="test-password")
        self.user.user_permissions.add(Permission.objects.get(codename="can_generate_checklist"))
        OpenAISettings.objects.create(api_key="sk-test")
        upload = SimpleUploadedFile(
            "concept-note.docx",
            build_readable_docx("Marimba workshop for village students."),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        output_text = json.dumps(
            {
                "event_title": "Marimba Workshop",
                "source_note": "Generated from uploaded Event Concept Note.",
                "sections": [
                    {
                        "title": "Quick checklist",
                        "items": ["Confirm with organizer: meeting point.", "Bring water and notebook."],
                    }
                ],
            }
        )

        with patch("resources.checklist_generator.OpenAI") as openai:
            openai.return_value.responses.create.return_value = SimpleNamespace(output_text=output_text)
            response = self.client.post(reverse("api-checklist-generate"), {"concept_note": upload})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF-"))
        openai.return_value.responses.create.assert_called_once()
        call_kwargs = openai.return_value.responses.create.call_args.kwargs
        self.assertEqual(call_kwargs["model"], "gpt-5.5")
        self.assertEqual(call_kwargs["reasoning"], {"effort": "medium"})

    def test_generate_checklist_rejects_invalid_docx(self):
        self.client.login(username="volunteer", password="test-password")
        self.user.user_permissions.add(Permission.objects.get(codename="can_generate_checklist"))
        upload = SimpleUploadedFile(
            "concept-note.docx",
            b"not a docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        response = self.client.post(reverse("api-checklist-generate"), {"concept_note": upload})

        self.assertEqual(response.status_code, 400)
        self.assertIn("readable DOCX", response.json()["detail"])

    def test_generate_checklist_rejects_empty_docx(self):
        self.client.login(username="volunteer", password="test-password")
        self.user.user_permissions.add(Permission.objects.get(codename="can_generate_checklist"))
        upload = SimpleUploadedFile(
            "empty.docx",
            build_readable_docx("", include_heading=False),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        response = self.client.post(reverse("api-checklist-generate"), {"concept_note": upload})

        self.assertEqual(response.status_code, 400)
        self.assertIn("does not contain readable text", response.json()["detail"])

    def test_generate_checklist_requires_openai_key(self):
        self.client.login(username="volunteer", password="test-password")
        self.user.user_permissions.add(Permission.objects.get(codename="can_generate_checklist"))
        upload = SimpleUploadedFile(
            "concept-note.docx",
            build_readable_docx("Marimba workshop for village students."),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        response = self.client.post(reverse("api-checklist-generate"), {"concept_note": upload})

        self.assertEqual(response.status_code, 503)
        self.assertIn("OpenAI API key is not configured", response.json()["detail"])

    def test_create_checklist_job_persists_pdf_for_preview_and_download(self):
        self.client.login(username="volunteer", password="test-password")
        self.user.user_permissions.add(Permission.objects.get(codename="can_generate_checklist"))
        OpenAISettings.objects.create(api_key="sk-test", checklist_queue_timeout_minutes=45)
        upload = SimpleUploadedFile(
            "concept-note.docx",
            build_readable_docx("Marimba workshop for village students."),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        output_text = json.dumps(
            {
                "event_title": "Marimba Workshop",
                "source_note": "Generated from uploaded Event Concept Note.",
                "sections": [{"title": "Quick checklist", "items": ["Bring water and notebook."]}],
            }
        )

        with patch("resources.checklist_generator.OpenAI") as openai:
            openai.return_value.responses.create.return_value = SimpleNamespace(output_text=output_text)
            response = self.client.post(reverse("api-checklist-job-create"), {"concept_note": upload})

        self.assertEqual(response.status_code, 200)
        job_payload = response.json()["job"]
        self.assertEqual(job_payload["status"], "done")
        self.assertTrue(job_payload["previewUrl"])
        self.assertTrue(job_payload["downloadUrl"])

        list_response = self.client.get(reverse("api-checklist-job-list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()["jobs"]), 1)

        preview_response = self.client.get(reverse("api-checklist-job-preview", args=[job_payload["id"]]))
        self.assertEqual(preview_response.status_code, 200)
        self.assertEqual(preview_response["Content-Type"], "application/pdf")
        self.assertIn("inline", preview_response["Content-Disposition"])

        download_response = self.client.get(reverse("api-checklist-job-download", args=[job_payload["id"]]))
        self.assertEqual(download_response.status_code, 200)
        self.assertIn("attachment", download_response["Content-Disposition"])

    def test_checklist_job_list_hides_expired_jobs(self):
        self.client.login(username="volunteer", password="test-password")
        self.user.user_permissions.add(Permission.objects.get(codename="can_generate_checklist"))
        expired_job = ChecklistJob.objects.create(
            user=self.user,
            input_filename="expired.docx",
            concept_note=SimpleUploadedFile("expired.docx", build_readable_docx(), content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            output_filename="expired.pdf",
            status=ChecklistJob.Status.DONE,
            expires_at=timezone.now() - timezone.timedelta(minutes=1),
        )
        expired_job.generated_pdf.save("expired.pdf", ContentFile(build_simple_pdf("Expired", "Expired")), save=True)

        response = self.client.get(reverse("api-checklist-job-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["jobs"], [])
