from django.contrib import admin

from app.hospitaldetails.models import Repository, Hospital, RecordsInfo

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ['name', 'town', 'postcode', 'closed', 'foundation_year', 'last_updated_at']
    list_filter = ['closed', 'more_research_required', 'pre_1974_county', 'post_1974_county']
    search_fields = ['name', 'previous_names', 'town', 'postcode']
    readonly_fields = ['created_at', 'last_updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'name_since', 'previous_names')
        }),
        ('Address', {
            'fields': ('street_1', 'street_2', 'town', 'postcode', 'address_since', 'previous_locations')
        }),
        ('Trust', {
            'fields': ('trust', 'trust_since', 'previous_trusts')
        }),
        ('Dates', {
            'fields': ('foundation_year', 'foundation_year_approximate', 'closed', 'closure_date', 'closure_year_approximate')
        }),
        ('Pre-1948 Classification', {
            'fields': ('pre_1948_status', 'pre_1948_status_info', 'pre_1948_type', 'pre_1948_type_info')
        }),
        ('Post-1948 Classification', {
            'fields': ('post_1948_status', 'post_1948_status_info', 'post_1948_type', 'post_1948_type_info')
        }),
        ('Geographic Context', {
            'fields': ('pre_1974_county', 'post_1974_county', 'post_1996_county', 'regional_board', 'management_committee')
        }),
        ('Authorities', {
            'fields': ('pre_1982_regional_authority', 'post_1982_regional_authority', 'pre_1982_district_authority', 'post_1982_district_authority')
        }),
        ('Additional Info', {
            'fields': ('other_information', 'more_research_required', 'researcher_comment', 'created_at', 'last_updated_at')
        }),
    )
    
    filter_horizontal = ['pre_1948_status', 'post_1948_status', 'pre_1948_type', 'post_1948_type']

@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'town', 'postcode', 'archon_code', 'last_updated_at']
    search_fields = ['name', 'town', 'postcode']
    readonly_fields = ['created_at', 'last_updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'archon_code', 'repository_code')
        }),
        ('Address', {
            'fields': ('street_1', 'street_2', 'town', 'postcode', 'county', 'contact_details')
        }),
        ('Additional Info', {
            'fields': ('mailshot', 'more_research_required', 'researcher_comment', 'created_at', 'last_updated_at')
        }),
    )

@admin.register(RecordsInfo)
class RecordsInfoAdmin(admin.ModelAdmin):
    list_display = ['hospital', 'repository', 'last_updated_at']
    list_filter = ['more_research_required']
    search_fields = ['hospital__name', 'repository__name', 'finding_aids_details']
    readonly_fields = ['created_at', 'last_updated_at']
    
    fieldsets = (
        ('Associations', {
            'fields': ('hospital', 'repository')
        }),
        ('Records Information', {
            'fields': ('finding_aids', 'finding_aids_location', 'finding_aids_details')
        }),
        ('Additional Info', {
            'fields': ('more_research_required', 'researcher_comment', 'created_at', 'last_updated_at')
        }),
    )

    filter_horizontal = ['finding_aids', 'finding_aids_location']