import pytest
from pytest_django.asserts import assertRedirects, assertFormError
from django.urls import reverse
import random

from http import HTTPStatus

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


@pytest.mark.django_db(transaction=True)
def test_anonymous_user_cant_create_comment(client, news, form_data):
    url = reverse('news:detail', kwargs={'pk': news.pk})
    before_create_count = Comment.objects.count()
    client.post(url, data=form_data)
    after_create_count = Comment.objects.count()
    assert after_create_count == before_create_count


def test_user_can_create_comment(author, author_client, news, form_data):
    url = reverse('news:detail', kwargs={'pk': news.pk})
    before_create_pks = set(Comment.objects.values_list('pk', flat=True))
    before_create_count = Comment.objects.count()
    response = author_client.post(url, data=form_data)
    after_create_pks = set(Comment.objects.values_list('pk', flat=True))
    new_pk = (after_create_pks - before_create_pks).pop()
    after_create_count = Comment.objects.count()
    expected_url = url + '#comments'
    assertRedirects(response, expected_url)
    assert after_create_count == before_create_count + 1
    comment = Comment.objects.get(pk=new_pk)
    try:
        assert comment.text == form_data['text']
    except KeyError:
        pytest.fail('Ошибка: Ключ "text" отсутствует в словаре form_data')
    assert comment.news == news
    assert comment.author == author


def test_user_cant_use_bad_words(admin_client, news):
    bad_word = random.choice(BAD_WORDS)
    bad_words_data = {'text': f'Какой-то text, {bad_word}, еще text'}
    url = reverse('news:detail', kwargs={'pk': news.pk})
    before_create_count = Comment.objects.count()
    response = admin_client.post(url, data=bad_words_data)
    assertFormError(response, form='form', field='text', errors=WARNING)
    after_create_count = Comment.objects.count()
    assert after_create_count == before_create_count


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
    before_create_count = Comment.objects.count()
    response = author_client.post(url)
    assertRedirects(response,
                    reverse('news:detail',
                            kwargs={'pk': news.pk}) + '#comments')
    after_create_count = Comment.objects.count()
    assert after_create_count == before_create_count - 1
