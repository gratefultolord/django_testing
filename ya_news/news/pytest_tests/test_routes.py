import pytest
from pytest_django.asserts import assertRedirects

from http import HTTPStatus

from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',
    ('news:home', 'users:login', 'users:logout', 'users:signup')
)
def test_pages_availability_for_anonymous_user(client, name):
    url = reverse(name)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_news_detail_page_avaialbility_for_anonymous_user(client, news):
    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete'),
)
def test_comment_edit_and_delete_for_author(client, author, comment, name):
    client.force_login(author)
    url = reverse(name, kwargs={'pk': comment.pk})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete'),
)
def test_anonymous_user_redirect_to_login(client, name, comment):
    login_url = reverse('users:login')
    url = reverse(name, kwargs={'pk': comment.pk})
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
        (pytest.lazy_fixture('admin_client'), HTTPStatus.NOT_FOUND),
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK)
    )
)
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete'),
)
def test_pages_availability_for_different_users(
    parametrized_client, name, comment, expected_status
):
    url = reverse(name, kwargs={'pk': comment.pk})
    response = parametrized_client.get(url)
    assert response.status_code == expected_status
