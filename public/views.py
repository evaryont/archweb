from datetime import datetime
from operator import attrgetter

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import cache_control

from devel.models import MasterKey, PGPSignature
from main.models import Arch, Repo, Donor
from mirrors.models import MirrorUrl
from news.models import News
from .utils import get_recent_updates

@cache_control(max_age=300)
def index(request):
    if request.user.is_authenticated():
        pkgs = get_recent_updates(testing=True, staging=True)
    else:
        pkgs = get_recent_updates()
    context = {
        'news_updates': News.objects.order_by('-postdate', '-id')[:15],
        'pkg_updates': pkgs,
    }
    return render(request, 'public/index.html', context)

USER_LISTS = {
    'devs': {
        'user_type': 'Developers',
        'user_title': 'Developer',
        'description': "This is a list of the current Arch Linux Developers. They maintain the [core] and [extra] package repositories in addition to doing any other developer duties.",
    },
    'tus': {
        'user_type': 'Trusted Users',
        'user_title': 'Trusted User',
        'description': "Here are all your friendly Arch Linux Trusted Users who are in charge of the [community] repository.",
    },
    'fellows': {
        'user_type': 'Fellows',
        'user_title': 'Fellow',
        'description': "Below you can find a list of ex-developers (aka project fellows). These folks helped make Arch what it is today. Thanks!",
    },
}

@cache_control(max_age=300)
def userlist(request, user_type='devs'):
    users = User.objects.order_by(
            'first_name', 'last_name').select_related('userprofile')
    if user_type == 'devs':
        users = users.filter(is_active=True, groups__name="Developers")
    elif user_type == 'tus':
        users = users.filter(is_active=True, groups__name="Trusted Users")
    elif user_type == 'fellows':
        users = users.filter(is_active=False,
                groups__name__in=["Developers", "Trusted Users"])
    else:
        raise Http404

    users = users.distinct()
    context = USER_LISTS[user_type].copy()
    context['users'] = users
    return render(request, 'public/userlist.html', context)

@cache_control(max_age=300)
def donate(request):
    context = {
        'donors': Donor.objects.filter(visible=True).order_by('name'),
    }
    return render(request, 'public/donate.html', context)

@cache_control(max_age=300)
def download(request):
    mirror_urls = MirrorUrl.objects.select_related('mirror').filter(
            protocol__default=True,
            mirror__public=True, mirror__active=True, mirror__isos=True)
    sort_by = attrgetter('real_country.name', 'mirror.name')
    mirror_urls = sorted(mirror_urls, key=sort_by)
    context = {
        'releng_iso_url': settings.ISO_LIST_URL,
        'releng_pxeboot_url': settings.PXEBOOT_URL,
        'mirror_urls': mirror_urls,
    }
    return render(request, 'public/download.html', context)

@cache_control(max_age=300)
def feeds(request):
    repos = Repo.objects.all()
    if not request.user.is_authenticated():
        repos = repos.filter(staging=False)
    context = {
        'arches': Arch.objects.all(),
        'repos': repos,
    }
    return render(request, 'public/feeds.html', context)

@cache_control(max_age=300)
def keys(request):
    users = User.objects.filter(is_active=True).select_related(
            'userprofile__pgp_key').order_by('first_name', 'last_name')
    user_key_ids = frozenset(user.userprofile.pgp_key[-16:] for user in users
            if user.userprofile.pgp_key)

    not_expired = Q(expires__gt=datetime.utcnow) | Q(expires__isnull=True)
    master_keys = MasterKey.objects.select_related('owner', 'revoker',
            'owner__userprofile', 'revoker__userprofile').filter(
            revoked__isnull=True)
    master_key_ids = frozenset(key.pgp_key[-16:] for key in master_keys)

    sig_counts = PGPSignature.objects.filter(not_expired, valid=True,
            signee__in=user_key_ids).values_list('signer').annotate(
            Count('signer'))
    sig_counts = dict((key_id[-16:], ct) for key_id, ct in sig_counts)

    for key in master_keys:
        key.signature_count = sig_counts.get(key.pgp_key[-16:], 0)

    # frozenset because we are going to do lots of __contains__ lookups
    signatures = frozenset(PGPSignature.objects.filter(
            not_expired, valid=True).values_list('signer', 'signee'))

    restrict = Q(signer__in=user_key_ids) & Q(signee__in=user_key_ids)
    cross_signatures = PGPSignature.objects.filter(restrict,
            not_expired, valid=True).order_by('created')

    context = {
        'keys': master_keys,
        'active_users': users,
        'signatures': signatures,
        'cross_signatures': cross_signatures,
    }
    return render(request, 'public/keys.html', context)

# vim: set ts=4 sw=4 et:
