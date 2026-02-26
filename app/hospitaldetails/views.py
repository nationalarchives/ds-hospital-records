from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

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

    context = {
        "query": query,
        "results": results,
        "paginator": paginator,
        "page_obj": page_obj,
        "page_numbers": page_numbers,
    }
    return render(request, "hospitaldetails/search.html", context)


def hospital_detail(request, id):
    """Display details for a specific hospital."""
    hospital = get_object_or_404(Hospital, id=id)

    # Get related records info for this hospital
    records = (
        RecordsInfo.objects.filter(hospital=hospital).select_related("repository").all()
    )

    context = {
        "hospital": hospital,
        "records": records,
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

    context = {
        "repository": repository,
        "records": records,
    }
    return render(request, "hospitaldetails/repository_detail.html", context)


def home_page(request):
    """Display the home page."""
    return render(request, "hospitaldetails/home.html")
