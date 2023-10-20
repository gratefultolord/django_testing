import pytest

from pytest_django.asserts import assertRedirects, assertFormError

from django.urls import reverse

from http import HTTPStatus

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


@pytest.mark.django_db(transaction=True)
def test_anonymous_user_cant_create_comment(client, news, form_data):
    url = reverse('news:detail', kwargs={'pk': news.pk})
    client.post(url, data=form_data)
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_user_can_create_comment(author, author_client, news, form_data):
    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = author_client.post(url, data=form_data)
    expected_url = url + '#comments'
    assertRedirects(response, expected_url)
    assert Comment.objects.count() == 1
    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


def test_user_cant_use_bad_words(admin_client, news):
    bad_words_data = {'text': f'Какой-то text, {BAD_WORDS[0]}, еще text'}
    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = admin_client.post(url, data=bad_words_data)
    assertFormError(response, form='form', field='text', errors=WARNING)
    comments_count = Comment.objects.count()
    expected_comments = 0
    assert comments_count == expected_comments


def test_author_can_edit_comment(author,
                                 author_client, comment, form_data, news):
    url = reverse('news:edit', kwargs={'pk': news.pk})
    response = author_client.post(url, form_data)
    assertRedirects(response,
                    reverse('news:detail',
                            kwargs={'pk': news.pk}) + '#comments')
    comment.refresh_from_db()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


def test_user_cant_edit_comment_of_another_user(admin_client,
                                                comment, form_data, news):
    url = reverse('news:edit', kwargs={'pk': news.pk})
    response = admin_client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == form_data['text']


def test_user_cant_delete_comment_of_another_user(admin_client, comment):
    url = reverse('news:delete', kwargs={'pk': comment.news.pk})
    response = admin_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1


def test_author_can_delete_comment(author_client, comment, news):
    url = reverse('news:delete', kwargs={'pk': comment.news.pk})
    response = author_client.post(url)
    assertRedirects(response,
                    reverse('news:detail',
                            kwargs={'pk': news.pk}) + '#comments')
    comments_count = Comment.objects.count()
    assert comments_count == 0
