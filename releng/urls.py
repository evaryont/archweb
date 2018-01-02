from django.conf.urls import include, url

from .views import ReleaseListView, ReleaseDetailView
from releng import views

feedback_patterns = [
    url(r'^$', views.test_results_overview, name='releng-test-overview'),
    url(r'^submit/$', views.submit_test_result, name='releng-test-submit'),
    url(r'^thanks/$', views.submit_test_thanks, name='releng-test-thanks'),
    url(r'^iso/(?P<iso_id>\d+)/$', views.test_results_iso, name='releng-results-iso'),
    url(r'^(?P<option>.+)/(?P<value>\d+)/$', views.test_results_for, name='releng-results-for'),
    url(r'^iso/overview/$', views.iso_overview, name='releng-iso-overview'),
]

releases_patterns = [
    url(r'^$', ReleaseListView.as_view(), name='releng-release-list'),
    url(r'^json/$', views.releases_json, name='releng-release-list-json'),
    url(r'^(?P<version>[-.\w]+)/$', ReleaseDetailView.as_view(), name='releng-release-detail'),
    url(r'^(?P<version>[-.\w]+)/torrent/$', views.release_torrent, name='releng-release-torrent'),
]

netboot_patterns = [
    url(r'^archlinux\.ipxe$', views.netboot_config, name='releng-netboot-config'),
    url(r'^$', views.netboot_info, name='releng-netboot-info')
]

urlpatterns = [
    url(r'^feedback/', include(feedback_patterns)),
    url(r'^releases/', include(releases_patterns)),
    url(r'^netboot/', include(netboot_patterns)),
]

# vim: set ts=4 sw=4 et:
