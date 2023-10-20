from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()
OBJECT_LIST = 'object_list'


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Антон Антонов')
        cls.note = Note.objects.create(
            title='Тестовая заметка', text='Текст', author=cls.author
        )

    def test_note_in_object_list(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse('notes:list'))
        notes = response.context[OBJECT_LIST]
        self.assertIn(self.note, notes)

    def test_note_not_in_other_list(self):
        self.client.force_login(self.author)
        another_user_note = Note.objects.create(
            title='Другая заметка',
            text='Другой текст',
            author=self.reader)
        response = self.client.get(reverse('notes:list'))
        notes = response.context[OBJECT_LIST]
        self.assertIn(self.note, notes)
        self.assertNotIn(another_user_note, notes)

    def test_note_form(self):
        self.client.force_login(self.author)
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIsInstance(response.context['form'], NoteForm)
