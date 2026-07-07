import base64
import datetime
import json
from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import (
    Hospital,
    Post1948Status,
    Post1948Type,
    Pre1948Status,
    Pre1948Type,
    RecordsInfo,
    Repository,
)


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
    # params: dict of search params (e.g. {'q': 'ashford', 'page': '2'})
    json_str = json.dumps(params, sort_keys=True)
    b64 = base64.urlsafe_b64encode(json_str.encode()).decode()
    return b64.rstrip("=")


def _parse_year(value):
    if value is None:
        return None

    parsed = str(value).strip()
    if not parsed:
        return None

    if not parsed.isdigit():
        return None

    return int(parsed)


def _parse_int_list(values):
    parsed_values = []

    for value in values:
        try:
            parsed_values.append(int(value))
        except (TypeError, ValueError):
            continue

    return parsed_values


def search(request):
    """Search for hospitals by name or town."""
    query = request.GET.get("q", "").strip()
    open_closed_status = request.GET.get("open_closed_status", "all")
    if open_closed_status not in {"all", "open", "closed"}:
        open_closed_status = "all"

    foundation_year_from = _parse_year(request.GET.get("foundation_year_from"))
    foundation_year_to = _parse_year(request.GET.get("foundation_year_to"))

    current_year = datetime.date.today().year
    effective_foundation_year_from = foundation_year_from
    effective_foundation_year_to = foundation_year_to

    if foundation_year_from is None and foundation_year_to is not None:
        effective_foundation_year_from = 0
    if foundation_year_to is None and foundation_year_from is not None:
        effective_foundation_year_to = current_year

    pre_1948_status_ids = _parse_int_list(request.GET.getlist("pre_1948_status"))
    post_1948_status_ids = _parse_int_list(request.GET.getlist("post_1948_status"))
    pre_1948_type_ids = _parse_int_list(request.GET.getlist("pre_1948_type"))
    post_1948_type_ids = _parse_int_list(request.GET.getlist("post_1948_type"))

    has_active_search = any(
        [
            query,
            open_closed_status != "all",
            foundation_year_from is not None,
            foundation_year_to is not None,
            pre_1948_status_ids,
            post_1948_status_ids,
            pre_1948_type_ids,
            post_1948_type_ids,
        ]
    )

    results = Hospital.objects.none()
    page_obj = None
    paginator = None
    page_numbers = []

    if has_active_search:
        # Search in hospital name, previous names, and town
        results = Hospital.objects.all()

        if query:
            results = results.filter(
                Q(name__icontains=query)
                | Q(previous_names__icontains=query)
                | Q(town__icontains=query)
            )

        if open_closed_status == "open":
            results = results.filter(closed=False)
        elif open_closed_status == "closed":
            results = results.filter(closed=True)

        if (
            effective_foundation_year_from is not None
            and effective_foundation_year_to is not None
        ):
            # Filter by year founded within the selected range.
            results = results.filter(
                foundation_year__isnull=False,
                foundation_year__gte=effective_foundation_year_from,
                foundation_year__lte=effective_foundation_year_to,
            )

        if pre_1948_status_ids:
            results = results.filter(pre_1948_status__id__in=pre_1948_status_ids)
        if post_1948_status_ids:
            results = results.filter(post_1948_status__id__in=post_1948_status_ids)
        if pre_1948_type_ids:
            results = results.filter(pre_1948_type__id__in=pre_1948_type_ids)
        if post_1948_type_ids:
            results = results.filter(post_1948_type__id__in=post_1948_type_ids)

        results = results.distinct().order_by("name")

        paginator = Paginator(results, 10)
        page_obj = paginator.get_page(request.GET.get("page"))
        results = page_obj.object_list
        page_numbers = _build_page_numbers(page_obj.number, paginator.num_pages)

    breadcrumbs = _hospital_records_breadcrumbs()

    search_params = {}
    if query:
        search_params["q"] = query
    if open_closed_status != "all":
        search_params["open_closed_status"] = open_closed_status
    if foundation_year_from is not None:
        search_params["foundation_year_from"] = str(foundation_year_from)
    if foundation_year_to is not None:
        search_params["foundation_year_to"] = str(foundation_year_to)
    if pre_1948_status_ids:
        search_params["pre_1948_status"] = [str(value) for value in pre_1948_status_ids]
    if post_1948_status_ids:
        search_params["post_1948_status"] = [str(value) for value in post_1948_status_ids]
    if pre_1948_type_ids:
        search_params["pre_1948_type"] = [str(value) for value in pre_1948_type_ids]
    if post_1948_type_ids:
        search_params["post_1948_type"] = [str(value) for value in post_1948_type_ids]

    search_hash = None
    if search_params:
        hash_params = dict(search_params)
        if page_obj and page_obj.number:
            hash_params["page"] = page_obj.number
        search_hash = encode_search_params(hash_params)

    pagination_query = urlencode(search_params, doseq=True)

    pre_1948_status_options = Pre1948Status.objects.all()
    post_1948_status_options = Post1948Status.objects.all()
    pre_1948_type_options = Pre1948Type.objects.all()
    post_1948_type_options = Post1948Type.objects.all()

    context = {
        "query": query,
        "results": results,
        "paginator": paginator,
        "page_obj": page_obj,
        "page_numbers": page_numbers,
        "has_active_search": has_active_search,
        "breadcrumbs": breadcrumbs,
        "search_hash": search_hash,
        "open_closed_status": open_closed_status,
        "foundation_year_from": foundation_year_from,
        "foundation_year_to": foundation_year_to,
        "pre_1948_status_options": pre_1948_status_options,
        "post_1948_status_options": post_1948_status_options,
        "pre_1948_type_options": pre_1948_type_options,
        "post_1948_type_options": post_1948_type_options,
        "selected_pre_1948_status_ids": pre_1948_status_ids,
        "selected_post_1948_status_ids": post_1948_status_ids,
        "selected_pre_1948_type_ids": pre_1948_type_ids,
        "selected_post_1948_type_ids": post_1948_type_ids,
        "pagination_query": pagination_query,
    }
    return render(request, "hospitaldetails/search.html", context)


def decode_search_params(hash_str):
    # hash_str: base64 encoded string
    padded = hash_str + "=" * (-len(hash_str) % 4)
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
