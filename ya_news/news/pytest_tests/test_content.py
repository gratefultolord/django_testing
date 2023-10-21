import pytest

from django.conf import settings
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.usefixtures('all_news')
def test_news_count(author_client):
    url = reverse('news:home')
    response = author_client.get(url)
    object_list = response.context.get('object_list', None)
    news_count = len(object_list)
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
@pytest.mark.usefixtures('all_news')
def test_news_order(author_client):
    url = reverse('news:home')
    response = author_client.get(url)
    object_list = response.context.get('object_list', None)
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
@pytest.mark.usefixtures('news', 'all_comments')
def test_comments_order(author_client, comment):
    url = reverse('news:detail', kwargs={'pk': comment.news.pk})
    response = author_client.get(url)
    comments = response.context['news'].comment_set.all()
    all_comments = [comment.created for comment in comments]
    sorted_comments = sorted(all_comments)
    assert all_comments == sorted_comments


@pytest.mark.django_db
def test_comment_form_availability_for_authenticated_user(comment,
                                                          author_client):
    url = reverse('news:detail', kwargs={'pk': comment.news.pk})
    response = author_client.get(url)
    assert 'form' in response.context


@pytest.mark.django_db
def test_comment_form_availability_for_anonymous_user(comment, client):
    url = reverse('news:detail', kwargs={'pk': comment.news.pk})
    response = client.get(url)
    assert 'form' not in response.context
