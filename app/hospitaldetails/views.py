from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Hospital, RecordsInfo, Repository


def search(request):
    """Search for hospitals by name or town."""
    query = request.GET.get("q", "").strip()
    results = []

    if query:
        # Search in hospital name, previous names, and town
        results = Hospital.objects.filter(
            Q(name__icontains=query)
            | Q(previous_names__icontains=query)
            | Q(town__icontains=query)
        ).order_by("name")

    context = {
        "query": query,
        "results": results,
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

    # Get related records info for this repository
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
