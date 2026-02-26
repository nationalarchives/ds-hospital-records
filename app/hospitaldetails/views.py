from django.core.paginator import Paginator
from django.db.models import Q
from urllib.parse import urlencode, parse_qs
import base64
import json

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Hospital, RecordsInfo, Repository


def _build_page_numbers(current_page, total_pages, window=1, edges=1):
    pages = []

    for page_number in range(1, total_pages + 1):
        in_edges = page_number <= edges or page_number > total_pages - edges
        in_window = current_page - window <= page_number <= current_page + window

        if in_edges or in_window:
            pages.append(page_number)
        elif pages and pages[-1] is not None:
            pages.append(None)

    return pages


def _hospital_records_breadcrumbs():
    return [
        {"text": "Home", "href": reverse("main:index")},
        {
            "text": "Hospital records",
            "href": reverse("hospitaldetails:home_page"),
        },
    ]


def encode_search_params(params):
    import base64, json
    json_str = json.dumps(params, sort_keys=True)
    b64 = base64.urlsafe_b64encode(json_str.encode()).decode()
    return b64.rstrip('=')

def search(request):
    """Search for hospitals by name or town."""
    query = request.GET.get("q", "").strip()
    results = Hospital.objects.none()
    page_obj = None
    paginator = None
    page_numbers = []

    if query:
        # Search in hospital name, previous names, and town
        results = Hospital.objects.filter(
            Q(name__icontains=query)
            | Q(previous_names__icontains=query)
            | Q(town__icontains=query)
        ).order_by("name")

        paginator = Paginator(results, 10)
        page_obj = paginator.get_page(request.GET.get("page"))
        results = page_obj.object_list
        page_numbers = _build_page_numbers(page_obj.number, paginator.num_pages)

    breadcrumbs = _hospital_records_breadcrumbs()

    search_hash = None
    if query or (page_obj and page_obj.number):
        search_params = {}
        if query:
            search_params["q"] = query
        if page_obj and page_obj.number:
            search_params["page"] = page_obj.number
        search_hash = encode_search_params(search_params)

    context = {
        "query": query,
        "results": results,
        "paginator": paginator,
        "page_obj": page_obj,
        "page_numbers": page_numbers,
        "breadcrumbs": breadcrumbs,
        "search_hash": search_hash,
    }
    return render(request, "hospitaldetails/search.html", context)


def encode_search_params(params):
    # params: dict of search params (e.g. {'q': 'ashford', 'page': '2'})
    json_str = json.dumps(params, sort_keys=True)
    b64 = base64.urlsafe_b64encode(json_str.encode()).decode()
    return b64.rstrip('=')

def decode_search_params(hash_str):
    # hash_str: base64 encoded string
    padded = hash_str + '=' * (-len(hash_str) % 4)
    try:
        json_str = base64.urlsafe_b64decode(padded.encode()).decode()
        return json.loads(json_str)
    except Exception:
        return {}

def hospital_detail(request, id):
    """Display details for a specific hospital."""
    hospital = get_object_or_404(Hospital, id=id)

    # Get related records info for this hospital
    records = (
        RecordsInfo.objects.filter(hospital=hospital).select_related("repository").all()
    )

    search_hash = request.GET.get("search", "").strip()
    search_params = {}
    if search_hash:
        search_params = decode_search_params(search_hash)
    else:
        query = request.GET.get("q", "").strip()
        page = request.GET.get("page", "").strip()
        if query:
            search_params["q"] = query
        if page:
            search_params["page"] = page

    back_link_href = reverse("hospitaldetails:search")
    if search_params:
        back_link_href = f"{back_link_href}?{urlencode(search_params)}"

    context = {
        "hospital": hospital,
        "records": records,
        "back_link_href": back_link_href,
    }
    return render(request, "hospitaldetails/hospital_detail.html", context)


def repository_detail(request, id):
    """Display details for a specific repository."""
    repository = get_object_or_404(Repository, id=id)

    if repository.archon_url:
        return redirect(repository.archon_url)

    records = (
        RecordsInfo.objects.filter(repository=repository)
        .select_related("hospital")
        .all()
    )

    breadcrumbs = _hospital_records_breadcrumbs() + [
        {"text": "Search hospitals", "href": reverse("hospitaldetails:search")}
    ]

    context = {
        "repository": repository,
        "records": records,
        "breadcrumbs": breadcrumbs,
    }
    return render(request, "hospitaldetails/repository_detail.html", context)


def home_page(request):
    """Display the home page."""
    breadcrumbs = [{"text": "Home", "href": reverse("main:index")}]
    return render(
        request,
        "hospitaldetails/home.html",
        {"breadcrumbs": breadcrumbs},
    )
