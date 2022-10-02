from django import forms
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from feincms.module.page.models import Page

from form_designer.models import FIELD_TYPES, Form, FormSubmission


def validate_honeypot(form, data, **kwargs):
    if data.get("honeypot"):
        raise forms.ValidationError("Hello honeypot")


Form.CONFIG_OPTIONS.append(
    ("honeypot", {"title": "Honeypot", "validate": validate_honeypot})
)


class FormsTest(TestCase):
    def test_forms(self):
        form = Form.objects.create(
            title="Test contact form",
            config={"email": {"email": "info@example.com"}, "save_fs": {}},
        )
        form.fields.create(ordering=0, title="Subject", name="subject", type="text")
        form.fields.create(ordering=1, title="Email", name="email", type="email")
        form.fields.create(ordering=2, title="Body", name="body", type="longtext")
        form.fields.create(
            ordering=3,
            title="Please call me",
            name="please-call-me",
            type="checkbox",
            is_required=False,
        )
        form.fields.create(
            ordering=4,
            title="Radio Select",
            name="radio",
            type="radio",
            choices="one,two what,three",
            default_value="two what",
        )
        form.fields.create(
            ordering=5,
            title="Date",
            name="date",
            type="date",
            is_required=False,
        )

        form_class = form.form_class()
        form_instance = form_class()

        self.assertListEqual(
            [field.name for field in form_instance],
            ["subject", "email", "body", "please-call-me", "radio", "date"],
        )

        page = Page.objects.create(override_url="/", title="")
        page.formcontent_set.create(
            region="main",
            ordering=0,
            form=form,
            success_message="Thanks, we will get back to you",
        )

        response = self.client.get("/")

        self.assertContains(response, 'method="post"', 1)
        self.assertContains(response, f'action="#form{form.id}"', 1)
        self.assertContains(
            response,
            "<input",
            10,  # csrf, subject, email, checkbox, _formcontent, submit, radio*3, date
        )
        self.assertContains(response, "<textarea", 1)
        self.assertContains(
            response, 'value="two-what" required id="id_fc1-radio_1" checked', 1
        )
        self.assertContains(response, 'type="date"', 1)

        response = self.client.post("/")

        self.assertContains(response, "This field is required", 4)

        # Not this form
        response = self.client.post("/", {"_formcontent": -1})

        self.assertNotContains(response, "This field is required")

        response = self.client.post(
            "/",
            {
                "_formcontent": form.id,
                f"fc{form.id}-subject": "Test",
                f"fc{form.id}-email": "invalid",
                f"fc{form.id}-body": "Hello World",
                f"fc{form.id}-radio": "one",
            },
        )

        self.assertNotContains(response, "This field is required")

        self.assertContains(
            response, "Enter a valid e", 1  # Django 1.4 has e-mail, 1.5 and up email
        )

        response = self.client.post(
            "/",
            {
                "_formcontent": form.id,
                f"fc{form.id}-subject": "Test",
                f"fc{form.id}-email": "valid@example.com",
                f"fc{form.id}-body": "Hello World",
                f"fc{form.id}-radio": "one",
                f"fc{form.id}-date": "2022-10-02",
            },
        )

        self.assertContains(response, "Thanks, we will get back to you", 1)

        self.assertNotContains(response, "<form")

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]

        self.assertListEqual(message.to, ["info@example.com"])
        self.assertEqual(message.from_email, "no-reply@example.com")
        self.assertEqual(message.subject, "Test contact form")
        self.assertIn("Subject:\nTest\n", message.body)
        self.assertIn("Email:\nvalid@example.com\n", message.body)
        self.assertIn("Body:\nHello World\n", message.body)
        self.assertIn("Please call me:\nØ\n", message.body)
        self.assertIn("Date:\n2022-10-02\n", message.body)

        # Exactly one submission
        submission = FormSubmission.objects.get()

        self.assertEqual(
            form.submissions_data(submissions=[submission]),
            [
                {
                    "submission": submission,
                    "data": [
                        {"name": "subject", "title": "Subject", "value": "Test"},
                        {
                            "name": "email",
                            "title": "Email",
                            "value": "valid@example.com",
                        },
                        {"name": "body", "title": "Body", "value": "Hello World"},
                        {
                            "name": "please-call-me",
                            "title": "Please call me",
                            "value": False,
                        },
                        {"name": "radio", "title": "Radio Select", "value": "one"},
                        {"name": "date", "title": "Date", "value": "2022-10-02"},
                    ],
                }
            ],
        )

        # Export the submission
        User.objects.create_superuser("admin", "admin@example.com", "password")
        self.client.login(username="admin", password="password")
        response = self.client.get(
            "/admin/form_designer/form/{}/export_submissions/".format(
                submission.form_id
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        response = self.client.get(
            f"/admin/form_designer/formsubmission/{submission.id}/change/"
        )
        self.assertContains(response, "<dt>Body</dt>")

        FormSubmission.objects.all().delete()
        response = self.client.get(
            "/admin/form_designer/form/{}/export_submissions/".format(
                submission.form_id
            )
        )
        self.assertRedirects(
            response, f"/admin/form_designer/form/{submission.form_id}/change/"
        )

    def test_admin(self):
        User.objects.create_superuser("admin", "admin@example.com", "password")
        self.client.login(username="admin", password="password")

        response = self.client.get("/admin/form_designer/form/add/")
        self.assertEqual(response.status_code, 200)  # Oh well...

        data = {
            "title": "Test form",
            "_is_active_save_fs": "on",
            "_is_active_email": "on",
            "initial-config": "{}",
            "config": "{}",
            "email_email": "bla@example.com,blabbb@example.com",
            "fields-TOTAL_FORMS": 9,
            "fields-INITIAL_FORMS": 0,
            "fields-MIN_NUM_FORMS": 0,
            "fields-MAX_NUM_FORMS": 1000,
        }
        for i in range(9):
            data[f"fields-{i}-ordering"] = (i + 1) * 10
            data[f"fields-{i}-title"] = f"title-{i}"
            data[f"fields-{i}-name"] = f"name-{i}"
            data[f"fields-{i}-type"] = FIELD_TYPES[i]["type"]
            data[f"fields-{i}-choices"] = ""

        # Validation failure because of missing choices
        response = self.client.post("/admin/form_designer/form/add/", data)
        self.assertEqual(response.status_code, 200)

        for i in range(9):
            if FIELD_TYPES[i]["type"] in {"select", "radio", "multiple-select"}:
                data[f"fields-{i}-choices"] = "a,b,c,d"

        data["fields-0-choices"] = "invalid"
        # Validation failure because of choices where there should be none
        response = self.client.post("/admin/form_designer/form/add/", data)
        self.assertEqual(response.status_code, 200)

        data["fields-0-choices"] = ""
        response = self.client.post("/admin/form_designer/form/add/", data)
        self.assertRedirects(response, "/admin/form_designer/form/")

        data["fields-4-type"] = ""  # No crash, but no success either
        response = self.client.post("/admin/form_designer/form/add/", data)
        self.assertEqual(response.status_code, 200)

        # Basic smoke test
        form = Form.objects.get()
        self.assertEqual(set(form.config), {"email", "save_fs"})
        form_class = form.form_class()

        self.assertEqual(form.title, "Test form")
        self.assertEqual(len(form_class().fields), 9)

        # The additional formsets exist
        response = self.client.get(f"/admin/form_designer/form/{form.id}/change/")
        self.assertContains(response, 'id="id_email_email"')
        self.assertContains(response, "blabbb@example.com")

    def test_honeypot(self):
        form = Form.objects.create(
            title="Test honeypot form",
            config={"honeypot": {}},
        )
        form.fields.create(ordering=0, title="Subject", name="subject", type="text")
        form.fields.create(
            ordering=0,
            title="honeypot",
            name="honeypot",
            type="hidden",
            is_required=False,
        )

        page = Page.objects.create(override_url="/", title="")
        page.formcontent_set.create(
            region="main",
            ordering=0,
            form=form,
            success_message="Thanks, we will get back to you",
        )

        response = self.client.post(
            "/",
            {
                "_formcontent": form.id,
                f"fc{form.id}-subject": "Test",
                f"fc{form.id}-honeypot": "honey",
            },
        )

        self.assertContains(response, "Hello honeypot")

    def test_submission(self):
        form = Form.objects.create(
            title="Test contact form",
            config={"email": {"email": "info@example.com"}, "save_fs": {}},
        )
        form.fields.create(ordering=0, title="Subject", name="subject", type="text")
        form.fields.create(
            ordering=1, title="Email", name="email", _old_name="e mail", type="email"
        )

        s1 = FormSubmission.objects.create(
            form=form,
            data={
                "subject": "blub",
                "email": "a@example.com",
            },
        )
        s2 = FormSubmission.objects.create(
            form=form,
            data={
                "subject": "blub",
                "e mail": "a@example.com",
            },
        )

        form.fields.create(ordering=2, title="test", name="test", type="text")

        self.assertEqual(
            form.submissions_data(),
            [
                {
                    "submission": s2,
                    "data": [
                        {"name": "subject", "title": "Subject", "value": "blub"},
                        {"name": "email", "title": "Email", "value": "a@example.com"},
                        {"name": "test", "title": "test", "value": None},
                        {
                            "name": "e mail",
                            "title": "e mail (removed field)",
                            "value": "a@example.com",
                        },
                    ],
                },
                {
                    "submission": s1,
                    "data": [
                        {"name": "subject", "title": "Subject", "value": "blub"},
                        {"name": "email", "title": "Email", "value": "a@example.com"},
                        {"name": "test", "title": "test", "value": None},
                        {
                            "name": "e mail",
                            "title": "e mail (removed field)",
                            "value": None,
                        },
                    ],
                },
            ],
        )

    def test_email_to_author(self):
        form = Form.objects.create(
            title="Test contact form",
            config={
                "email": {"email": "info@example.com", "author_email_field": "mmm"}
            },
        )
        form.fields.create(ordering=0, title="Subject", name="subject", type="text")
        form.fields.create(ordering=1, title="Email", name="mmm", type="email")

        page = Page.objects.create(override_url="/", title="")
        page.formcontent_set.create(
            region="main",
            ordering=0,
            form=form,
            success_message="Thanks, we will get back to you",
        )

        response = self.client.post(
            "/",
            {
                "_formcontent": form.id,
                f"fc{form.id}-subject": "Test",
                f"fc{form.id}-mmm": "test@example.org",
            },
        )
        self.assertContains(response, "Thanks, we will get back to you", 1)

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]

        self.assertListEqual(message.to, ["info@example.com"])
        self.assertListEqual(message.cc, ["test@example.org"])
        self.assertEqual(message.from_email, "no-reply@example.com")
        self.assertEqual(message.subject, "Test contact form")
        self.assertIn("Subject:\nTest\n", message.body)
        self.assertIn("Email:\ntest@example.org\n", message.body)
