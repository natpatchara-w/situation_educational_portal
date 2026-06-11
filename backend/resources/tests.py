import json
import uuid
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings
from django.utils import timezone
from django.urls import reverse
from docx import Document

from .checklist_generator import extract_docx_text, generate_checklist_payload, normalize_checklist_payload, redact_sensitive_text
from .cleanup import delete_expired_checklist_jobs
from .models import ChecklistJob, OpenAISettings, Resource, ThrottleRecord
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
        uuid.UUID(payload["resources"][0]["id"])

    def test_cors_allows_configured_frontend_origin(self):
        response = self.client.options(reverse("api-resource-list"), HTTP_ORIGIN="http://localhost:5173")

        self.assertEqual(response["Access-Control-Allow-Origin"], "http://localhost:5173")
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")

    def test_cors_blocks_unconfigured_origin(self):
        response = self.client.options(reverse("api-resource-list"), HTTP_ORIGIN="https://evil.example")

        self.assertNotIn("Access-Control-Allow-Origin", response)

    @override_settings(CSP_ENABLED=True, CSP_REPORT_ONLY=False, CSP_POLICY="default-src 'self'")
    def test_csp_header_can_be_enabled(self):
        self.client.login(username="volunteer", password="test-password")

        response = self.client.get(reverse("api-resource-list"))

        self.assertEqual(response["Content-Security-Policy"], "default-src 'self'")

    @override_settings(CSP_ENABLED=True, CSP_REPORT_ONLY=True, CSP_POLICY="default-src 'self'")
    def test_csp_report_only_header_can_be_enabled(self):
        self.client.login(username="volunteer", password="test-password")

        response = self.client.get(reverse("api-resource-list"))

        self.assertEqual(response["Content-Security-Policy-Report-Only"], "default-src 'self'")

    def test_search_and_category_filters_resources(self):
        self.client.login(username="volunteer", password="test-password")

        response = self.client.get(reverse("api-resource-list"), {"search": "tsunami", "category": "educational"})

        self.assertEqual(response.status_code, 200)
        resources = response.json()["resources"]
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]["title"], "Tsunami Education Guide")

    def test_download_serves_active_pdf(self):
        self.client.login(username="volunteer", password="test-password")

        response = self.client.get(reverse("api-resource-download", args=[self.checklist.public_id]))

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

        response = self.client.get(reverse("api-resource-download", args=[docx.public_id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.assertIn("editable-checklist", response["Content-Disposition"])
        self.assertIn(".docx", response["Content-Disposition"])

    def test_download_rejects_missing_resource(self):
        self.client.login(username="volunteer", password="test-password")

        response = self.client.get(reverse("api-resource-download", args=[uuid.uuid4()]))

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

    @override_settings(RESOURCE_MAX_UPLOAD_BYTES=8)
    def test_resource_upload_rejects_oversized_file(self):
        resource = Resource(
            title="Large PDF",
            category=Resource.Category.CHECKLIST,
            pdf_file=SimpleUploadedFile("large.pdf", b"%PDF-" + b"x" * 20, content_type="application/pdf"),
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

    @override_settings(CHECKLIST_JOB_THROTTLE_LIMIT=1)
    def test_checklist_job_create_is_throttled(self):
        self.client.login(username="volunteer", password="test-password")
        self.user.user_permissions.add(Permission.objects.get(codename="can_generate_checklist"))
        OpenAISettings.objects.create(api_key="sk-test")

        for _ in range(2):
            upload = SimpleUploadedFile(
                "concept-note.docx",
                build_readable_docx("Marimba workshop for village students."),
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            with patch("resources.tasks.generate_checklist_job.delay"):
                response = self.client.post(reverse("api-checklist-job-create"), {"concept_note": upload})

        self.assertEqual(response.status_code, 429)

    def test_extract_docx_text_reads_paragraphs(self):
        upload = SimpleUploadedFile(
            "concept-note.docx",
            build_readable_docx("Marimba workshop for village students."),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        text = extract_docx_text(upload)

        self.assertIn("Event Concept Note", text)
        self.assertIn("Marimba workshop", text)

    def test_redact_sensitive_text_masks_obvious_personal_data_and_tokens(self):
        redacted = redact_sensitive_text("Email jane@example.org, call +1 555-111-2222, api_key=sk_secretvalue12345")

        self.assertIn("[redacted-email]", redacted)
        self.assertIn("[redacted-phone]", redacted)
        self.assertIn("[redacted-secret]", redacted)

    @override_settings(CHECKLIST_MAX_SECTIONS=1, CHECKLIST_MAX_ITEMS_PER_SECTION=1)
    def test_normalize_checklist_payload_bounds_model_output(self):
        payload = normalize_checklist_payload(
            {
                "event_title": "x" * 300,
                "source_note": "y" * 700,
                "sections": [
                    {"title": "First", "items": ["a", "b"]},
                    {"title": "Second", "items": ["c"]},
                ],
            }
        )

        self.assertEqual(len(payload["event_title"]), 160)
        self.assertEqual(len(payload["source_note"]), 500)
        self.assertEqual(len(payload["sections"]), 1)
        self.assertEqual(payload["sections"][0]["items"], ["a"])

    def test_generate_checklist_redacts_prompt_before_openai_call(self):
        output_text = json.dumps(
            {
                "event_title": "Safe Workshop",
                "source_note": "Generated.",
                "sections": [{"title": "Quick checklist", "items": ["Bring water."]}],
            }
        )

        with patch("resources.checklist_generator.OpenAI") as openai:
            openai.return_value.responses.create.return_value = SimpleNamespace(output_text=output_text)
            generate_checklist_payload("Contact jane@example.org and api_key=sk_secretvalue12345", "sk-test")

        user_prompt = openai.return_value.responses.create.call_args.kwargs["input"][1]["content"]
        self.assertNotIn("jane@example.org", user_prompt)
        self.assertNotIn("sk_secretvalue12345", user_prompt)
        self.assertIn("[redacted-email]", user_prompt)

    def test_generate_checklist_endpoint_requires_queue_endpoint(self):
        self.client.login(username="volunteer", password="test-password")
        self.user.user_permissions.add(Permission.objects.get(codename="can_generate_checklist"))

        response = self.client.post(reverse("api-checklist-generate"))

        self.assertEqual(response.status_code, 410)
        self.assertIn("queued", response.json()["detail"])

    def test_openai_api_key_is_encrypted_at_rest(self):
        settings = OpenAISettings.objects.create(api_key="sk-test")

        with connection.cursor() as cursor:
            cursor.execute("SELECT api_key FROM resources_openaisettings WHERE id = %s", [settings.id])
            stored_value = cursor.fetchone()[0]

        self.assertNotEqual(stored_value, "sk-test")
        self.assertTrue(stored_value.startswith("fernet$"))
        self.assertEqual(OpenAISettings.objects.get(id=settings.id).api_key, "sk-test")

    def test_generate_checklist_rejects_invalid_docx(self):
        self.client.login(username="volunteer", password="test-password")
        self.user.user_permissions.add(Permission.objects.get(codename="can_generate_checklist"))
        upload = SimpleUploadedFile(
            "concept-note.docx",
            b"not a docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            response = self.client.post(reverse("api-checklist-job-create"), {"concept_note": upload})

        self.assertEqual(response.status_code, 202)
        job = ChecklistJob.objects.get()
        self.assertEqual(job.status, ChecklistJob.Status.ERROR)
        self.assertIn("valid DOCX", job.error_message)

    @override_settings(CHECKLIST_MAX_UPLOAD_BYTES=8)
    def test_generate_checklist_rejects_oversized_docx(self):
        self.client.login(username="volunteer", password="test-password")
        self.user.user_permissions.add(Permission.objects.get(codename="can_generate_checklist"))
        upload = SimpleUploadedFile(
            "large.docx",
            build_readable_docx("Large concept note."),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            response = self.client.post(reverse("api-checklist-job-create"), {"concept_note": upload})

        self.assertEqual(response.status_code, 202)
        job = ChecklistJob.objects.get()
        self.assertEqual(job.status, ChecklistJob.Status.ERROR)
        self.assertIn("Event Concept Note must be", job.error_message)

    @override_settings(DOCX_MAX_COMPRESSION_RATIO=1)
    def test_generate_checklist_rejects_high_compression_docx(self):
        self.client.login(username="volunteer", password="test-password")
        self.user.user_permissions.add(Permission.objects.get(codename="can_generate_checklist"))
        upload = SimpleUploadedFile(
            "compressed.docx",
            build_readable_docx("A" * 2000),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            response = self.client.post(reverse("api-checklist-job-create"), {"concept_note": upload})

        self.assertEqual(response.status_code, 202)
        job = ChecklistJob.objects.get()
        self.assertEqual(job.status, ChecklistJob.Status.ERROR)
        self.assertIn("compression ratio", job.error_message)

    def test_generate_checklist_rejects_empty_docx(self):
        self.client.login(username="volunteer", password="test-password")
        self.user.user_permissions.add(Permission.objects.get(codename="can_generate_checklist"))
        upload = SimpleUploadedFile(
            "empty.docx",
            build_readable_docx("", include_heading=False),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            response = self.client.post(reverse("api-checklist-job-create"), {"concept_note": upload})

        self.assertEqual(response.status_code, 202)
        job = ChecklistJob.objects.get()
        self.assertEqual(job.status, ChecklistJob.Status.ERROR)
        self.assertIn("does not contain readable text", job.error_message)

    def test_generate_checklist_requires_openai_key(self):
        self.client.login(username="volunteer", password="test-password")
        self.user.user_permissions.add(Permission.objects.get(codename="can_generate_checklist"))
        upload = SimpleUploadedFile(
            "concept-note.docx",
            build_readable_docx("Marimba workshop for village students."),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            response = self.client.post(reverse("api-checklist-job-create"), {"concept_note": upload})

        self.assertEqual(response.status_code, 202)
        job = ChecklistJob.objects.get()
        self.assertEqual(job.status, ChecklistJob.Status.ERROR)
        self.assertIn("OpenAI API key is not configured", job.error_message)

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

        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            with patch("resources.checklist_generator.OpenAI") as openai:
                openai.return_value.responses.create.return_value = SimpleNamespace(output_text=output_text)
                response = self.client.post(reverse("api-checklist-job-create"), {"concept_note": upload})

        self.assertEqual(response.status_code, 202)
        job_payload = response.json()["job"]
        uuid.UUID(job_payload["id"])
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

    def test_cleanup_deletes_expired_job_files(self):
        expired_job = ChecklistJob.objects.create(
            user=self.user,
            input_filename="expired.docx",
            concept_note=SimpleUploadedFile("expired.docx", build_readable_docx(), content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            output_filename="expired.pdf",
            status=ChecklistJob.Status.DONE,
            expires_at=timezone.now() - timezone.timedelta(minutes=1),
        )
        expired_job.generated_pdf.save("expired.pdf", ContentFile(build_simple_pdf("Expired", "Expired")), save=True)
        concept_path = expired_job.concept_note.path
        pdf_path = expired_job.generated_pdf.path

        deleted = delete_expired_checklist_jobs()

        self.assertEqual(deleted, 1)
        self.assertFalse(ChecklistJob.objects.filter(id=expired_job.id).exists())
        self.assertFalse(Path(concept_path).exists())
        self.assertFalse(Path(pdf_path).exists())


class ThrottleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="volunteer", password="test-password")

    @override_settings(LOGIN_THROTTLE_LIMIT=1)
    def test_api_login_is_throttled(self):
        first = self.client.post(
            reverse("api-login"),
            data=json.dumps({"username": "volunteer", "password": "wrong"}),
            content_type="application/json",
        )
        second = self.client.post(
            reverse("api-login"),
            data=json.dumps({"username": "volunteer", "password": "wrong"}),
            content_type="application/json",
        )

        self.assertEqual(first.status_code, 400)
        self.assertEqual(second.status_code, 429)
        self.assertTrue(ThrottleRecord.objects.filter(scope="api_login").exists())

    @override_settings(ADMIN_LOGIN_THROTTLE_LIMIT=1)
    def test_admin_login_is_throttled(self):
        first = self.client.post("/admin/login/", {"username": "admin", "password": "wrong"})
        second = self.client.post("/admin/login/", {"username": "admin", "password": "wrong"})

        self.assertNotEqual(first.status_code, 429)
        self.assertEqual(second.status_code, 429)
