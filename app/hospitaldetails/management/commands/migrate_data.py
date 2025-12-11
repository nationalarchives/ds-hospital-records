import os
import pymssql
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from app.hospitaldetails.models import (
    RegionalBoard, ManagementCommittee, 
    Pre1982RegionalAuthority, Post1982RegionalAuthority,
    Pre1982DistrictAuthority, Post1982DistrictAuthority,
    Hospital, RecordsInfo, Repository,
    Pre1948Status, Post1948Status, Pre1948Type, Post1948Type,
    Pre1974County, Post1974County, Post1996County,
    FindingAids, FindingAidsLocation
)


class Command(BaseCommand):
    help = 'Migrate data from MSSQL database to Django Postgres database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            default=os.getenv('MSSQL_HOST'),
            help='MSSQL server host'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=int(os.getenv('MSSQL_PORT', '1433')),
            help='MSSQL server port'
        )
        parser.add_argument(
            '--database',
            type=str,
            default=os.getenv('MSSQL_DATABASE'),
            help='MSSQL database name'
        )
        parser.add_argument(
            '--user',
            type=str,
            default=os.getenv('MSSQL_USER'),
            help='MSSQL username'
        )
        parser.add_argument(
            '--password',
            type=str,
            default=os.getenv('MSSQL_PASSWORD'),
            help='MSSQL password'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without saving to database'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before migration (WARNING: This will delete all existing records)'
        )
    
    def get_mssql_connection(self, host, port, database, user, password):
        """Establish connection to MSSQL database"""
        try:
            conn = pymssql.connect(
                server=host,
                port=port,
                database=database,
                user=user,
                password=password,
                as_dict=True
            )
            self.stdout.write(self.style.SUCCESS(f'Connected to MSSQL database: {database}'))
            return conn
        except Exception as e:
            raise CommandError(f'Failed to connect to MSSQL: {str(e)}')
    
    def handle(self, *args, **options):
        # Validate required connection parameters
        required = ['host', 'database', 'user', 'password']
        missing = [param for param in required if not options.get(param)]
        if missing:
            raise CommandError(f'Missing required parameters: {", ".join(missing)}')
        
        # Connect to MSSQL
        conn = self.get_mssql_connection(
            options['host'],
            options['port'],
            options['database'],
            options['user'],
            options['password']
        )
        
        cursor = conn.cursor()
        dry_run = options['dry_run']
        clear_data = options['clear']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY-RUN mode - no data will be saved'))
        
        if clear_data and not dry_run:
            self.stdout.write(self.style.WARNING('CLEARING EXISTING DATA...'))
            self.clear_data()
        
        try:
            # First, ensure lookup tables are populated
            self.populate_lookup_tables()
            
            # Migrate reference/lookup tables before hospitals
            self.migrate_pre_1974_counties(cursor, dry_run)
            self.migrate_post_1974_counties(cursor, dry_run)
            self.migrate_post_1996_counties(cursor, dry_run)
            self.migrate_regional_boards(cursor, dry_run)
            self.migrate_management_committees(cursor, dry_run)
            self.migrate_pre_1982_regional_authorities(cursor, dry_run)
            self.migrate_post_1982_regional_authorities(cursor, dry_run)
            self.migrate_pre_1982_district_authorities(cursor, dry_run)
            self.migrate_post_1982_district_authorities(cursor, dry_run)
            
            # Migrate repositories before hospitals (since hospitals may reference them)
            self.migrate_repositories(cursor, dry_run)
            
            # Then migrate hospitals
            self.migrate_hospitals(cursor, dry_run)
            
            # Migrate records info (requires hospitals and repositories)
            self.migrate_records_info(cursor, dry_run)
            
            self.stdout.write(self.style.SUCCESS('Migration completed successfully'))
            
        except Exception as e:
            raise CommandError(f'Migration failed: {str(e)}')
        finally:
            cursor.close()
            conn.close()
    
    def populate_lookup_tables(self):
        """Populate lookup tables for status and type if they don't exist"""
        self.stdout.write('Ensuring lookup tables are populated...')
        
        # Pre-1948 Status options
        pre_1948_statuses = ['Voluntary', 'Poor Law', 'Local Authority', 'Private', 'Other']
        for status in pre_1948_statuses:
            Pre1948Status.objects.get_or_create(value=status)
        
        # Post-1948 Status options
        post_1948_statuses = ['NHS', 'Private', 'Trust', 'Other']
        for status in post_1948_statuses:
            Post1948Status.objects.get_or_create(value=status)
        
        # Pre-1948 Type options
        pre_1948_types = ['General', 'Isolation', 'Maternity', 'Mental', 'Tuberculosis', 
                          'Women', 'Children', 'Military', 'Other']
        for type_val in pre_1948_types:
            Pre1948Type.objects.get_or_create(value=type_val)
        
        # Post-1948 Type options
        post_1948_types = ['Acute', 'Geriatric', 'Maternity', 'Mental', 'Hospice', 
                           'Military', 'Other']
        for type_val in post_1948_types:
            Post1948Type.objects.get_or_create(value=type_val)
        
        # Finding Aids options
        finding_aids = ['Brief guide (BG)', 'Catalogue', 'Card index', 'Computerised']
        for aid in finding_aids:
            FindingAids.objects.get_or_create(value=aid)
        
        # Finding Aids Location options
        finding_aids_locations = ['Repository (AR)', 'Local Record Office (LRO)', 'National Register of Archives (NRA)', 'Wellcome Library (WIHM)', 'The National Archives (TNA)', 'Other']
        for location in finding_aids_locations:
            FindingAidsLocation.objects.get_or_create(value=location)
        
        self.stdout.write(self.style.SUCCESS('Lookup tables populated'))
    
    def clear_data(self):
        """Clear existing data from all tables in reverse order of dependencies"""
        # Clear in reverse order of dependencies
        count = RecordsInfo.objects.count()
        RecordsInfo.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {count} records from RecordsInfo'))
        
        count = Hospital.objects.count()
        Hospital.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {count} records from Hospital'))
        
        count = Repository.objects.count()
        Repository.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {count} records from Repository'))
        
        count = Post1982DistrictAuthority.objects.count()
        Post1982DistrictAuthority.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {count} records from Post1982DistrictAuthority'))
        
        count = Pre1982DistrictAuthority.objects.count()
        Pre1982DistrictAuthority.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {count} records from Pre1982DistrictAuthority'))
        
        count = Post1982RegionalAuthority.objects.count()
        Post1982RegionalAuthority.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {count} records from Post1982RegionalAuthority'))
        
        count = Pre1982RegionalAuthority.objects.count()
        Pre1982RegionalAuthority.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {count} records from Pre1982RegionalAuthority'))
        
        count = ManagementCommittee.objects.count()
        ManagementCommittee.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {count} records from ManagementCommittee'))
        
        count = RegionalBoard.objects.count()
        RegionalBoard.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {count} records from RegionalBoard'))
        
        count = Post1996County.objects.count()
        Post1996County.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {count} records from Post1996County'))
        
        count = Post1974County.objects.count()
        Post1974County.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {count} records from Post1974County'))
        
        count = Pre1974County.objects.count()
        Pre1974County.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {count} records from Pre1974County'))
    
    def make_timezone_aware(self, dt):
        """Make a datetime timezone-aware if it's naive"""
        if dt and timezone.is_naive(dt):
            return timezone.make_aware(dt)
        return dt
    
    def prepare_timestamps(self, input_date, last_updated_date):
        """Prepare timestamp fields for data dict, returning only non-null values"""
        timestamps = {}
        
        input_date = self.make_timezone_aware(input_date)
        last_updated_date = self.make_timezone_aware(last_updated_date)
        
        if input_date:
            timestamps['created_at'] = input_date
        elif last_updated_date:
            timestamps['created_at'] = last_updated_date
            
        if last_updated_date:
            timestamps['last_updated_at'] = last_updated_date
        elif input_date:
            timestamps['last_updated_at'] = input_date
        
        return timestamps
    
    def set_foreign_key_if_valid(self, obj, field_name, fk_id, model_class, error_label):
        """Set foreign key if valid, skip ID=1, set None if doesn't exist"""
        if fk_id and fk_id != 1:
            if model_class.objects.filter(id=fk_id).exists():
                setattr(obj, field_name, fk_id)
            else:
                self.stdout.write(
                    self.style.WARNING(f"{error_label} {fk_id} not found, setting to None")
                )
                setattr(obj, field_name, None)
        else:
            setattr(obj, field_name, None)
    
    def add_m2m_if_true(self, obj, m2m_field, condition, model_class, value):
        """Add many-to-many relationship if condition is true"""
        if condition:
            item = model_class.objects.get(value=value)
            m2m_field.add(item)
    
    @transaction.atomic
    def migrate_lookup_table(self, cursor, dry_run, config):
        """Generic method to migrate simple lookup tables with id and name fields"""
        self.stdout.write(f"Migrating {config['label']}...")
        
        cursor.execute(config['query'])
        rows = cursor.fetchall()
        
        self.stdout.write(f"Found {len(rows)} {config['label']}")
        
        created_count = 0
        
        for row in rows:
            try:
                item_id = row.get(config['id_field'])
                item_name = row.get(config['name_field'])
                
                if not item_name:
                    continue
                
                if not dry_run:
                    item, created = config['model'].objects.update_or_create(
                        id=item_id,
                        defaults={'name': item_name}
                    )
                    if created:
                        created_count += 1
                else:
                    self.stdout.write(f"Would create: {item_name} (ID: {item_id})")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing {config['label']} {row.get(config['name_field'])}: {str(e)}")
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f"{config['label']}: {created_count} created")
        )
    
    @transaction.atomic
    def migrate_pre_1974_counties(self, cursor, dry_run=False):
        """Migrate Pre-1974 counties from MSSQL"""
        self.migrate_lookup_table(cursor, dry_run, {
            'label': 'Pre-1974 Counties',
            'query': 'SELECT CountyPre74ID, CountyPre74 FROM dbo.tblRefCountyPre74',
            'id_field': 'CountyPre74ID',
            'name_field': 'CountyPre74',
            'model': Pre1974County
        })
    
    @transaction.atomic
    def migrate_post_1974_counties(self, cursor, dry_run=False):
        """Migrate Post-1974 counties from MSSQL"""
        self.migrate_lookup_table(cursor, dry_run, {
            'label': 'Post-1974 Counties',
            'query': 'SELECT CountyPost74ID, CountyPost74 FROM dbo.tblRefCountyPost74',
            'id_field': 'CountyPost74ID',
            'name_field': 'CountyPost74',
            'model': Post1974County
        })
    
    @transaction.atomic
    def migrate_post_1996_counties(self, cursor, dry_run=False):
        """Migrate Post-1996 counties from MSSQL"""
        self.migrate_lookup_table(cursor, dry_run, {
            'label': 'Post-1996 Counties',
            'query': 'SELECT CountyPost96ID, CountyPost96 FROM dbo.tblRefCountyPost96',
            'id_field': 'CountyPost96ID',
            'name_field': 'CountyPost96',
            'model': Post1996County
        })
    
    @transaction.atomic
    def migrate_regional_boards(self, cursor, dry_run=False):
        """Migrate Regional Boards from MSSQL"""
        self.migrate_lookup_table(cursor, dry_run, {
            'label': 'Regional Boards',
            'query': 'SELECT RegionalBoard1948ID, RegionalBoard1948 FROM dbo.tblRefRegionalBoard1948',
            'id_field': 'RegionalBoard1948ID',
            'name_field': 'RegionalBoard1948',
            'model': RegionalBoard
        })
    
    @transaction.atomic
    def migrate_management_committees(self, cursor, dry_run=False):
        """Migrate Management Committees from MSSQL"""
        self.migrate_lookup_table(cursor, dry_run, {
            'label': 'Management Committees',
            'query': 'SELECT ManagementCommittee1948ID, ManagementCommittee1948 FROM dbo.tblRefManagementCommittee1948',
            'id_field': 'ManagementCommittee1948ID',
            'name_field': 'ManagementCommittee1948',
            'model': ManagementCommittee
        })
    
    @transaction.atomic
    def migrate_pre_1982_regional_authorities(self, cursor, dry_run=False):
        """Migrate Pre-1982 Regional Authorities from MSSQL"""
        self.migrate_lookup_table(cursor, dry_run, {
            'label': 'Pre-1982 Regional Authorities',
            'query': 'SELECT RegionalAuthority1974ID, RegionalAuthority1974 FROM dbo.tblRefRegionalAuthority1974',
            'id_field': 'RegionalAuthority1974ID',
            'name_field': 'RegionalAuthority1974',
            'model': Pre1982RegionalAuthority
        })
    
    @transaction.atomic
    def migrate_post_1982_regional_authorities(self, cursor, dry_run=False):
        """Migrate Post-1982 Regional Authorities from MSSQL"""
        self.migrate_lookup_table(cursor, dry_run, {
            'label': 'Post-1982 Regional Authorities',
            'query': 'SELECT RegionalAuthority1982ID, RegionalAuthority1982 FROM dbo.tblRefRegionalAuthority1982',
            'id_field': 'RegionalAuthority1982ID',
            'name_field': 'RegionalAuthority1982',
            'model': Post1982RegionalAuthority
        })
    
    @transaction.atomic
    def migrate_pre_1982_district_authorities(self, cursor, dry_run=False):
        """Migrate Pre-1982 District Authorities from MSSQL"""
        self.migrate_lookup_table(cursor, dry_run, {
            'label': 'Pre-1982 District Authorities',
            'query': 'SELECT DistrictAuthority1974ID, DistrictAuthority1974 FROM dbo.tblRefDistrictAuthority1974',
            'id_field': 'DistrictAuthority1974ID',
            'name_field': 'DistrictAuthority1974',
            'model': Pre1982DistrictAuthority
        })
    
    @transaction.atomic
    def migrate_post_1982_district_authorities(self, cursor, dry_run=False):
        """Migrate Post-1982 District Authorities from MSSQL"""
        self.migrate_lookup_table(cursor, dry_run, {
            'label': 'Post-1982 District Authorities',
            'query': 'SELECT DistrictAuthority1982ID, DistrictAuthority1982 FROM dbo.tblRefDistrictAuthority1982',
            'id_field': 'DistrictAuthority1982ID',
            'name_field': 'DistrictAuthority1982',
            'model': Post1982DistrictAuthority
        })
    
    @transaction.atomic
    def migrate_hospitals(self, cursor, dry_run=False):
        """
        Migrate hospital records from MSSQL to Postgres.
        Adjust table name and field mappings according to your MSSQL schema.
        """
        self.stdout.write('Migrating hospitals...')
        
        query = """
            SELECT 
                Hospital_No
                ,PresentName
                ,PresentNameDate
                ,PreviousNames
                ,Street1
                ,Street2
                ,Town
                ,PostCode
                ,AddressFrom
                ,PreviousLocations
                ,PresentTrust
                ,PresentTrustDate
                ,PreviousTrusts
                ,FoundationDate
                ,FoundationDateApproximate
                ,Closed
                ,ClosureDate
                ,ClosureDateApproximate
                ,Pre1948Voluntary
                ,Pre1948PoorLaw
                ,Pre1948LocalAuthority
                ,Pre1948Private
                ,Pre1948OtherStatus
                ,Pre1948StatusInfo
                ,Post1948NHS
                ,Post1948Private
                ,Post1948Trust
                ,Post1948OtherStatus
                ,Post1948StatusInfo
                ,Pre1948General
                ,Pre1948Isolation
                ,Pre1948Maternity
                ,Pre1948Mental
                ,Pre1948Tuberculosis
                ,Pre1948Women
                ,Pre1948Children
                ,Pre1948Military
                ,Pre1948OtherType
                ,Pre1948TypeInfo
                ,Post1948Acute
                ,Post1948Geriatric
                ,Post1948Maternity
                ,Post1948Mental
                ,Post1948Hospice
                ,Post1948Military
                ,Post1948OtherType
                ,Post1948TypeInfo
                ,OtherInfoHistory
                ,MoreResearchReqd
                ,ResearcherInstruction
                ,InputDate
                ,LastUpdatedDate
                ,CountyPre74ID
                ,CountyPost74ID
                ,CountyPost96ID
                ,RegionalBoard1948ID
                ,ManagementCommittee1948ID
                ,RegionalAuthority1974ID
                ,DistrictAuthority1974ID
                ,RegionalAuthority1982ID
                ,DistrictAuthority1982ID
            FROM dbo.tblHospital
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()

        self.stdout.write(f'Found {len(rows)} hospitals to migrate')
        
        created_count = 0
        updated_count = 0
        
        for row in rows:
            try:
                # Map MSSQL fields to Django model fields
                hospital_data = {
                    'name': row.get('PresentName', ''),
                    'name_since': row.get('PresentNameDate'),
                    'previous_names': row.get('PreviousNames'),
                    'street_1': row.get('Street1'),
                    'street_2': row.get('Street2'),
                    'town': row.get('Town'),
                    'postcode': row.get('PostCode'),
                    'address_since': row.get('AddressFrom'),
                    'previous_locations': row.get('PreviousLocations'),
                    'trust': row.get('PresentTrust'),
                    'trust_since': row.get('PresentTrustDate'),
                    'previous_trusts': row.get('PreviousTrusts'),
                    'foundation_year': row.get('FoundationDate'),
                    'foundation_year_approximate': bool(row.get('FoundationDateApproximate', False)),
                    'closed': bool(row.get('Closed', False)),
                    'closure_date': row.get('ClosureDate'),
                    'closure_year_approximate': bool(row.get('ClosureDateApproximate', False)),
                    'pre_1948_status_info': row.get('Pre1948StatusInfo'),
                    'post_1948_status_info': row.get('Post1948StatusInfo'),
                    'pre_1948_type_info': row.get('Pre1948TypeInfo'),
                    'post_1948_type_info': row.get('Post1948TypeInfo'),
                    'other_information': row.get('OtherInfoHistory'),
                    'more_research_required': bool(row.get('MoreResearchReqd', False)),
                    'researcher_comment': row.get('ResearcherInstruction'),
                }
                
                # Add timestamps using helper method
                hospital_data.update(self.prepare_timestamps(row.get('InputDate'), row.get('LastUpdatedDate')))
                
                # Store foreign key IDs for later lookup
                fk_data = {
                    'pre_1974_county_id': row.get('CountyPre74ID'),
                    'post_1974_county_id': row.get('CountyPost74ID'),
                    'post_1996_county_id': row.get('CountyPost96ID'),
                    'regional_board_id': row.get('RegionalBoard1948ID'),
                    'management_committee_id': row.get('ManagementCommittee1948ID'),
                    'pre_1982_regional_authority_id': row.get('RegionalAuthority1974ID'),
                    'post_1982_regional_authority_id': row.get('RegionalAuthority1982ID'),
                    'pre_1982_district_authority_id': row.get('DistrictAuthority1974ID'),
                    'post_1982_district_authority_id': row.get('DistrictAuthority1982ID'),
                }
                
                # Get the original hospital ID from MSSQL
                hospital_id = row.get('Hospital_No')
                
                if not dry_run:
                    # Use update_or_create with the original ID
                    hospital, created = Hospital.objects.update_or_create(
                        id=hospital_id,
                        defaults=hospital_data
                    )
                    
                    # Handle Pre-1948 Status many-to-many relationships using helper method
                    hospital.pre_1948_status.clear()
                    self.add_m2m_if_true(hospital, hospital.pre_1948_status, row.get('Pre1948Voluntary'), Pre1948Status, 'Voluntary')
                    self.add_m2m_if_true(hospital, hospital.pre_1948_status, row.get('Pre1948PoorLaw'), Pre1948Status, 'Poor Law')
                    self.add_m2m_if_true(hospital, hospital.pre_1948_status, row.get('Pre1948LocalAuthority'), Pre1948Status, 'Local Authority')
                    self.add_m2m_if_true(hospital, hospital.pre_1948_status, row.get('Pre1948Private'), Pre1948Status, 'Private')
                    self.add_m2m_if_true(hospital, hospital.pre_1948_status, row.get('Pre1948OtherStatus'), Pre1948Status, 'Other')
                    
                    # Handle Post-1948 Status many-to-many relationships using helper method
                    hospital.post_1948_status.clear()
                    self.add_m2m_if_true(hospital, hospital.post_1948_status, row.get('Post1948NHS'), Post1948Status, 'NHS')
                    self.add_m2m_if_true(hospital, hospital.post_1948_status, row.get('Post1948Private'), Post1948Status, 'Private')
                    self.add_m2m_if_true(hospital, hospital.post_1948_status, row.get('Post1948Trust'), Post1948Status, 'Trust')
                    self.add_m2m_if_true(hospital, hospital.post_1948_status, row.get('Post1948OtherStatus'), Post1948Status, 'Other')
                    
                    # Handle Pre-1948 Type many-to-many relationships using helper method
                    hospital.pre_1948_type.clear()
                    self.add_m2m_if_true(hospital, hospital.pre_1948_type, row.get('Pre1948General'), Pre1948Type, 'General')
                    self.add_m2m_if_true(hospital, hospital.pre_1948_type, row.get('Pre1948Isolation'), Pre1948Type, 'Isolation')
                    self.add_m2m_if_true(hospital, hospital.pre_1948_type, row.get('Pre1948Maternity'), Pre1948Type, 'Maternity')
                    self.add_m2m_if_true(hospital, hospital.pre_1948_type, row.get('Pre1948Mental'), Pre1948Type, 'Mental')
                    self.add_m2m_if_true(hospital, hospital.pre_1948_type, row.get('Pre1948Tuberculosis'), Pre1948Type, 'Tuberculosis')
                    self.add_m2m_if_true(hospital, hospital.pre_1948_type, row.get('Pre1948Women'), Pre1948Type, 'Women')
                    self.add_m2m_if_true(hospital, hospital.pre_1948_type, row.get('Pre1948Children'), Pre1948Type, 'Children')
                    self.add_m2m_if_true(hospital, hospital.pre_1948_type, row.get('Pre1948Military'), Pre1948Type, 'Military')
                    self.add_m2m_if_true(hospital, hospital.pre_1948_type, row.get('Pre1948OtherType'), Pre1948Type, 'Other')
                    
                    # Handle Post-1948 Type many-to-many relationships using helper method
                    hospital.post_1948_type.clear()
                    self.add_m2m_if_true(hospital, hospital.post_1948_type, row.get('Post1948Acute'), Post1948Type, 'Acute')
                    self.add_m2m_if_true(hospital, hospital.post_1948_type, row.get('Post1948Geriatric'), Post1948Type, 'Geriatric')
                    self.add_m2m_if_true(hospital, hospital.post_1948_type, row.get('Post1948Maternity'), Post1948Type, 'Maternity')
                    self.add_m2m_if_true(hospital, hospital.post_1948_type, row.get('Post1948Mental'), Post1948Type, 'Mental')
                    self.add_m2m_if_true(hospital, hospital.post_1948_type, row.get('Post1948Hospice'), Post1948Type, 'Hospice')
                    self.add_m2m_if_true(hospital, hospital.post_1948_type, row.get('Post1948Military'), Post1948Type, 'Military')
                    self.add_m2m_if_true(hospital, hospital.post_1948_type, row.get('Post1948OtherType'), Post1948Type, 'Other')
                    
                    # Handle county foreign key relationships using helper method
                    self.set_foreign_key_if_valid(hospital, 'pre_1974_county_id', fk_data.get('pre_1974_county_id'), Pre1974County, 'Pre-1974 County')
                    self.set_foreign_key_if_valid(hospital, 'post_1974_county_id', fk_data.get('post_1974_county_id'), Post1974County, 'Post-1974 County')
                    self.set_foreign_key_if_valid(hospital, 'post_1996_county_id', fk_data.get('post_1996_county_id'), Post1996County, 'Post-1996 County')
                    
                    # Handle authority foreign key relationships using helper method
                    self.set_foreign_key_if_valid(hospital, 'regional_board_id', fk_data.get('regional_board_id'), RegionalBoard, 'Regional Board')
                    self.set_foreign_key_if_valid(hospital, 'management_committee_id', fk_data.get('management_committee_id'), ManagementCommittee, 'Management Committee')
                    self.set_foreign_key_if_valid(hospital, 'pre_1982_regional_authority_id', fk_data.get('pre_1982_regional_authority_id'), Pre1982RegionalAuthority, 'Pre-1982 Regional Authority')
                    self.set_foreign_key_if_valid(hospital, 'post_1982_regional_authority_id', fk_data.get('post_1982_regional_authority_id'), Post1982RegionalAuthority, 'Post-1982 Regional Authority')
                    self.set_foreign_key_if_valid(hospital, 'pre_1982_district_authority_id', fk_data.get('pre_1982_district_authority_id'), Pre1982DistrictAuthority, 'Pre-1982 District Authority')
                    self.set_foreign_key_if_valid(hospital, 'post_1982_district_authority_id', fk_data.get('post_1982_district_authority_id'), Post1982DistrictAuthority, 'Post-1982 District Authority')
                    
                    hospital.save()
                    
                    # Update created_at and last_updated_at with original values
                    # Using update() to bypass auto_now and auto_now_add
                    update_fields = {}
                    if row.get('InputDate'):
                        # Make datetime timezone-aware
                        input_date = row.get('InputDate')
                        if input_date and timezone.is_naive(input_date):
                            input_date = timezone.make_aware(input_date)
                        update_fields['created_at'] = input_date
                    
                    if row.get('LastUpdatedDate'):
                        # Make datetime timezone-aware
                        last_updated = row.get('LastUpdatedDate')
                        if last_updated and timezone.is_naive(last_updated):
                            last_updated = timezone.make_aware(last_updated)
                        update_fields['last_updated_at'] = last_updated
                    elif row.get('InputDate'):
                        # Use InputDate as fallback if LastUpdatedDate is not present
                        input_date = row.get('InputDate')
                        if input_date and timezone.is_naive(input_date):
                            input_date = timezone.make_aware(input_date)
                        update_fields['last_updated_at'] = input_date
                    
                    if update_fields:
                        Hospital.objects.filter(id=hospital.id).update(**update_fields)
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                else:
                    self.stdout.write(f"Would create/update: {hospital_data['name']}")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing hospital {row.get('PresentName')}: {str(e)}")
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Hospitals: {created_count} created, {updated_count} updated'
            )
        )
    
    @transaction.atomic
    def migrate_repositories(self, cursor, dry_run=False):
        """Migrate repository records from MSSQL to Postgres"""
        self.stdout.write('Migrating repositories...')
        
        query = """
            SELECT 
                Repository_No
                ,NRARepCode
                ,Name
                ,Street1
                ,Street2
                ,Town
                ,PostCode
                ,County
                ,MoreResearchReqd
                ,ResearcherInstruction
                ,ContactDetails
                ,Mailshot
                ,RepositoryCode
                ,InputDate
                ,LastUpdatedDate
            FROM dbo.tblRepository
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.stdout.write(f'Found {len(rows)} repositories to migrate')
        
        created_count = 0
        updated_count = 0
        
        for row in rows:
            try:
                # Make datetime values timezone-aware
                input_date = row.get('InputDate')
                if input_date and timezone.is_naive(input_date):
                    input_date = timezone.make_aware(input_date)
                
                last_updated_date = row.get('LastUpdatedDate')
                if last_updated_date and timezone.is_naive(last_updated_date):
                    last_updated_date = timezone.make_aware(last_updated_date)
                
                # Map MSSQL fields to Django model fields
                repository_data = {
                    'name': row.get('Name', ''),
                    'archon_code': row.get('NRARepCode'),
                    'repository_code': row.get('RepositoryCode'),
                    'street_1': row.get('Street1'),
                    'street_2': row.get('Street2'),
                    'town': row.get('Town'),
                    'postcode': row.get('PostCode'),
                    'county': row.get('County'),
                    'contact_details': row.get('ContactDetails'),
                    'mailshot': bool(row.get('Mailshot', False)),
                    'more_research_required': bool(row.get('MoreResearchReqd', False)),
                    'researcher_comment': row.get('ResearcherInstruction'),
                }
                
                # Add timestamps using helper method
                repository_data.update(self.prepare_timestamps(row.get('InputDate'), row.get('LastUpdatedDate')))
                
                # Get the original repository ID from MSSQL
                repository_id = row.get('Repository_No')
                
                if not dry_run:
                    # Use update_or_create with the original ID
                    repository, created = Repository.objects.update_or_create(
                        id=repository_id,
                        defaults=repository_data
                    )
                    
                    # Update created_at and last_updated_at with original values
                    # Using update() to bypass auto_now and auto_now_add
                    update_fields = {}
                    if input_date:
                        update_fields['created_at'] = input_date
                    
                    if last_updated_date:
                        update_fields['last_updated_at'] = last_updated_date
                    elif input_date:
                        # Use InputDate as fallback if LastUpdatedDate is not present
                        update_fields['last_updated_at'] = input_date
                    
                    if update_fields:
                        Repository.objects.filter(id=repository.id).update(**update_fields)
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                else:
                    self.stdout.write(f"Would create/update: {repository_data['name']}")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing repository {row.get('Name')}: {str(e)}")
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Repositories: {created_count} created, {updated_count} updated'
            )
        )
    
    @transaction.atomic
    def migrate_records_info(self, cursor, dry_run=False):
        """Migrate records info from MSSQL to Postgres"""
        self.stdout.write('Migrating records info...')
        
        query = """
            SELECT 
                Folder_No
                ,Hospital_No
                ,Repository_No
                ,RepositoryCode
                ,AdministrativeRecords
                ,AdministrativeStart
                ,AdministrativeFinish
                ,GeneralRecords
                ,GeneralStart
                ,GeneralFinish
                ,FinanceRecords
                ,FinanceStart
                ,FinanceFinish
                ,EstatesRecords
                ,EstatesStart
                ,EstatesFinish
                ,NursingRecords
                ,NursingStart
                ,NursingFinish
                ,StaffRecords
                ,StaffStart
                ,StaffFinish
                ,EphemeraRecords
                ,EphemeraStart
                ,EphemeraFinish
                ,PictorialRecords
                ,PictorialStart
                ,PictorialFinish
                ,PrivatePapersRecords
                ,PrivatePapersStart
                ,PrivatePapersFinish
                ,OtherRecords
                ,OtherStart
                ,OtherFinish
                ,PatientsRecords
                ,PatientsStart
                ,PatientsFinish
                ,AdmissionRecords
                ,AdmissionStart
                ,AdmissionFinish
                ,ClinicalRecords
                ,ClinicalStart
                ,ClinicalFinish
                ,RecordsNotes
                ,BriefGuideAids
                ,CatalogueAids
                ,CardIndexAids
                ,ComputerisedAids
                ,AidsWithRecords
                ,AidsAtLRO
                ,AidsAtNRA
                ,AidsAtWIHM
                ,AidsAtPRO
                ,AidsAtOther
                ,AidsDetails
                ,MoreResearchReqd
                ,ResearcherInstruction
                ,InputDate
                ,LastUpdatedDate
            FROM dbo.tblFolder
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.stdout.write(f'Found {len(rows)} records info to migrate')
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for row in rows:
            try:
                hospital_id = row.get('Hospital_No')
                repository_id = row.get('Repository_No')
                
                # Skip if hospital or repository doesn't exist
                if not hospital_id or not repository_id:
                    skipped_count += 1
                    continue
                
                if not Hospital.objects.filter(id=hospital_id).exists():
                    self.stdout.write(
                        self.style.WARNING(f"Hospital {hospital_id} not found, skipping folder {row.get('Folder_No')}")
                    )
                    skipped_count += 1
                    continue
                
                if not Repository.objects.filter(id=repository_id).exists():
                    self.stdout.write(
                        self.style.WARNING(f"Repository {repository_id} not found, skipping folder {row.get('Folder_No')}")
                    )
                    skipped_count += 1
                    continue
                
                # Update repository_code on the Repository if provided
                repository_code = row.get('RepositoryCode')
                if repository_code and not dry_run:
                    Repository.objects.filter(id=repository_id).update(repository_code=repository_code)
                
                # Map MSSQL fields to Django model fields
                records_data = {
                    'hospital_id': hospital_id,
                    'repository_id': repository_id,
                    'administrative_start': row.get('AdministrativeStart'),
                    'administrative_finish': row.get('AdministrativeFinish'),
                    'general_start': row.get('GeneralStart'),
                    'general_finish': row.get('GeneralFinish'),
                    'finance_start': row.get('FinanceStart'),
                    'finance_finish': row.get('FinanceFinish'),
                    'estates_start': row.get('EstatesStart'),
                    'estates_finish': row.get('EstatesFinish'),
                    'nursing_start': row.get('NursingStart'),
                    'nursing_finish': row.get('NursingFinish'),
                    'staff_start': row.get('StaffStart'),
                    'staff_finish': row.get('StaffFinish'),
                    'ephemera_start': row.get('EphemeraStart'),
                    'ephemera_finish': row.get('EphemeraFinish'),
                    'pictorial_start': row.get('PictorialStart'),
                    'pictorial_finish': row.get('PictorialFinish'),
                    'private_papers_start': row.get('PrivatePapersStart'),
                    'private_papers_finish': row.get('PrivatePapersFinish'),
                    'other_start': row.get('OtherStart'),
                    'other_finish': row.get('OtherFinish'),
                    'patients_start': row.get('PatientsStart'),
                    'patients_finish': row.get('PatientsFinish'),
                    'admission_start': row.get('AdmissionStart'),
                    'admission_finish': row.get('AdmissionFinish'),
                    'clinical_start': row.get('ClinicalStart'),
                    'clinical_finish': row.get('ClinicalFinish'),
                    'records_notes': row.get('RecordsNotes'),
                    'finding_aids_details': row.get('AidsDetails'),
                    'more_research_required': bool(row.get('MoreResearchReqd', False)),
                    'researcher_comment': row.get('ResearcherInstruction'),
                }
                
                # Add timestamps using helper method
                records_data.update(self.prepare_timestamps(row.get('InputDate'), row.get('LastUpdatedDate')))
                
                # Get the original folder ID from MSSQL
                folder_id = row.get('Folder_No')
                
                if not dry_run:
                    # Use update_or_create with the original ID
                    records_info, created = RecordsInfo.objects.update_or_create(
                        id=folder_id,
                        defaults=records_data
                    )
                    
                    # Handle finding aids many-to-many relationships using helper method
                    records_info.finding_aids.clear()
                    self.add_m2m_if_true(records_info, records_info.finding_aids, row.get('BriefGuideAids'), FindingAids, 'Brief guide (BG)')
                    self.add_m2m_if_true(records_info, records_info.finding_aids, row.get('CatalogueAids'), FindingAids, 'Catalogue')
                    self.add_m2m_if_true(records_info, records_info.finding_aids, row.get('CardIndexAids'), FindingAids, 'Card index')
                    self.add_m2m_if_true(records_info, records_info.finding_aids, row.get('ComputerisedAids'), FindingAids, 'Computerised')
                    
                    # Handle finding aids location many-to-many relationships using helper method
                    records_info.finding_aids_location.clear()
                    self.add_m2m_if_true(records_info, records_info.finding_aids_location, row.get('AidsWithRecords'), FindingAidsLocation, 'Repository (AR)')
                    self.add_m2m_if_true(records_info, records_info.finding_aids_location, row.get('AidsAtLRO'), FindingAidsLocation, 'Local Record Office (LRO)')
                    self.add_m2m_if_true(records_info, records_info.finding_aids_location, row.get('AidsAtNRA'), FindingAidsLocation, 'National Register of Archives (NRA)')
                    self.add_m2m_if_true(records_info, records_info.finding_aids_location, row.get('AidsAtWIHM'), FindingAidsLocation, 'Wellcome Library (WIHM)')
                    self.add_m2m_if_true(records_info, records_info.finding_aids_location, row.get('AidsAtPRO'), FindingAidsLocation, 'The National Archives (TNA)')
                    self.add_m2m_if_true(records_info, records_info.finding_aids_location, row.get('AidsAtOther'), FindingAidsLocation, 'Other')
                    
                    # Update created_at and last_updated_at with original values
                    update_fields = self.prepare_timestamps(row.get('InputDate'), row.get('LastUpdatedDate'))
                    if update_fields:
                        RecordsInfo.objects.filter(id=records_info.id).update(**update_fields)
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                else:
                    self.stdout.write(f"Would create/update records info for Hospital {hospital_id} / Repository {repository_id}")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing folder {row.get('Folder_No')}: {str(e)}")
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Records Info: {created_count} created, {updated_count} updated, {skipped_count} skipped'
            )
        )

