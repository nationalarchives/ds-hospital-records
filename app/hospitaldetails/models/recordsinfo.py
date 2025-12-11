import datetime

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class RecordsInfo(models.Model):
    hospital = models.ForeignKey('hospitaldetails.Hospital', on_delete=models.CASCADE, related_name='records_info')
    repository = models.ForeignKey('hospitaldetails.Repository', on_delete=models.CASCADE, related_name='records_info')
    administrative_start = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the administrative records start (YYYY)"
    )
    administrative_finish = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the administrative records finish (YYYY)"
    )
    general_start = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the general records start (YYYY)"
    )
    general_finish = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the general records finish (YYYY)"
    )
    finance_start = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the finance records start (YYYY)"
    )
    finance_finish = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the finance records finish (YYYY)"
    )
    estates_start = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the estates records start (YYYY)"
    )
    estates_finish = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the estates records finish (YYYY)"
    )
    nursing_start = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the nursing records start (YYYY)"
    )
    nursing_finish = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the nursing records finish (YYYY)"
    )
    staff_start = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the staff records start (YYYY)"
    )
    staff_finish = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the staff records finish (YYYY)"
    )
    ephemera_start = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the ephemera records start (YYYY)"
    )
    ephemera_finish = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the ephemera records finish (YYYY)"
    )
    pictorial_start = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the pictorial records start (YYYY)"
    )
    pictorial_finish = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the pictorial records finish (YYYY)"
    )
    private_papers_start = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the private papers records start (YYYY)"
    )
    private_papers_finish = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the private papers records finish (YYYY)"
    )
    other_start = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the other records start (YYYY)"
    )
    other_finish = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the other records finish (YYYY)"
    )
    patients_start = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the patients records start (YYYY)"
    )
    patients_finish = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the patients records finish (YYYY)"
    )
    admission_start = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the admission records start (YYYY)"
    )
    admission_finish = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the admission records finish (YYYY)"
    )
    clinical_start = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the clinical records start (YYYY)"
    )
    clinical_finish = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.date.today().year)],
        help_text="Year the clinical records finish (YYYY)"
    )
    records_notes = models.TextField(null=True, blank=True)
    finding_aids = models.ManyToManyField('hospitaldetails.FindingAids', blank=True, related_name='records_info')
    finding_aids_location = models.ManyToManyField('hospitaldetails.FindingAidsLocation', blank=True, related_name='records_info')
    finding_aids_details = models.TextField(null=True, blank=True)
    more_research_required = models.BooleanField(default=False)
    researcher_comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Records Info for {self.hospital.name} at {self.repository.name}"
    
    class Meta:
        ordering = ['hospital__name', 'repository__name']
