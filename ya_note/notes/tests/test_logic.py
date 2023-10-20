from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    NOTE_TITLE = 'Заголовок заметки'
    NOTE_TEXT = 'Текст заметки'
    SLUG = 'note-slug'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Иван Иванов')
        cls.url = reverse('notes:add')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.SLUG}
        cls.auth_client = Client()

    def test_anonymous_user_cant_create_note(self):
        self.client.logout()
        response = self.client.post(self.url, self.form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Note.objects.filter(title='Заголовок заметки').count(), 0)

    def test_authenticated_user_can_create_note(self):
        self.client.force_login(self.author)
        response = self.client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.slug, self.SLUG)
        self.assertEqual(note.author, self.author)

    def test_not_unique_slug(self):
        self.author_client.post(self.url, data=self.form_data)
        response = self.author_client.post(self.url, data=self.form_data)
        self.assertFormError(response,
                             'form', 'slug',
                             errors=(self.form_data['slug'] + WARNING))
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        self.author_client.post(self.url, data=self.form_data)
        self.form_data.pop('slug')
        Note.objects.get().delete()
        response = self.author_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditAndDelete(TestCase):
    NOTE_TITLE = 'Заголовок заметки'
    NOTE_TEXT = 'Текст заметки'
    SLUG = 'note-slug'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Иван Иванов')
        cls.reader = User.objects.create(username='Антон Антонов')
        cls.note = Note.objects.create(title=cls.NOTE_TITLE,
                                       text=cls.NOTE_TEXT,
                                       slug=cls.SLUG,
                                       author=cls.author)
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.SLUG}
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.edit_url = reverse('notes:edit', args=[cls.note.slug])
        cls.delete_url = reverse('notes:delete', args=[cls.note.slug])

    def test_user_can_delete_own_notes(self):
        response = self.author_client.post(self.delete_url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.filter(title='Test Note').count(), 0)

    def test_other_user_cant_delete_note(self):
        response = self.reader_client.post(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        self.assertEqual(self.note.text, self.NOTE_TEXT)
        self.assertEqual(self.note.slug, self.SLUG)

    def test_other_user_cant_edit_note(self):
        response = self.reader_client.post(self.edit_url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)
