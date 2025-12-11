from django.shortcuts import get_object_or_404, render

from .models import Hospital, Repository, RecordsInfo


def hospital_detail(request, id):
    """Display details for a specific hospital."""
    hospital = get_object_or_404(Hospital, id=id)
    
    # Get related records info for this hospital
    records = RecordsInfo.objects.filter(hospital=hospital).select_related('repository').all()
    
    context = {
        'hospital': hospital,
        'records': records,
    }
    return render(request, 'hospitaldetails/hospital_detail.html', context)


def repository_detail(request, id):
    """Display details for a specific repository."""
    repository = get_object_or_404(Repository, id=id)
    
    # Get related records info for this repository
    records = repository.recordsinfo_set.select_related('hospital').all()
    
    context = {
        'repository': repository,
        'records': records,
    }
    return render(request, 'hospitaldetails/repository_detail.html', context)
