import os
import pymssql
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
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
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY-RUN mode - no data will be saved'))
        
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
            
            # Then migrate hospitals
            self.migrate_hospitals(cursor, dry_run)
            
            # Add more migration methods here for other tables
            # self.migrate_records_info(cursor, dry_run)
            # self.migrate_repositories(cursor, dry_run)
            
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
        
        self.stdout.write(self.style.SUCCESS('Lookup tables populated'))
    
    @transaction.atomic
    def migrate_pre_1974_counties(self, cursor, dry_run=False):
        """Migrate Pre-1974 counties from MSSQL"""
        self.stdout.write('Migrating Pre-1974 counties...')
        
        query = """
        SELECT 
        [CountyPre74ID]
        ,[CountyPre74] 
        FROM dbo.tblRefCountyPre74
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.stdout.write(f'Found {len(rows)} Pre-1974 counties')
        
        created_count = 0
        
        for row in rows:
            try:
                county_id = row.get('CountyPre74ID')
                county_name = row.get('CountyPre74')
                
                if not county_name:
                    continue
                
                if not dry_run:
                    county, created = Pre1974County.objects.update_or_create(
                        id=county_id,
                        defaults={'name': county_name}
                    )
                    if created:
                        created_count += 1
                else:
                    self.stdout.write(f"Would create: {county_name} (ID: {county_id})")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing Pre-1974 county {row.get('CountyPre74')}: {str(e)}")
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Pre-1974 Counties: {created_count} created')
        )
    
    @transaction.atomic
    def migrate_post_1974_counties(self, cursor, dry_run=False):
        """Migrate Post-1974 counties from MSSQL"""
        self.stdout.write('Migrating Post-1974 counties...')
        
        query = """
        SELECT 
        [CountyPost74ID]
        ,[CountyPost74] 
        FROM dbo.tblRefCountyPost74
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.stdout.write(f'Found {len(rows)} Post-1974 counties')
        
        created_count = 0
        
        for row in rows:
            try:
                county_id = row.get('CountyPost74ID')
                county_name = row.get('CountyPost74')
                
                if not county_name:
                    continue
                
                if not dry_run:
                    county, created = Post1974County.objects.update_or_create(
                        id=county_id,
                        defaults={'name': county_name}
                    )
                    if created:
                        created_count += 1
                else:
                    self.stdout.write(f"Would create: {county_name} (ID: {county_id})")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing Post-1974 county {row.get('CountyPost74')}: {str(e)}")
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Post-1974 Counties: {created_count} created')
        )
    
    @transaction.atomic
    def migrate_post_1996_counties(self, cursor, dry_run=False):
        """Migrate Post-1996 counties from MSSQL"""
        self.stdout.write('Migrating Post-1996 counties...')
        
        query = """
        SELECT 
        [CountyPost96ID]
        ,[CountyPost96] 
        FROM dbo.tblRefCountyPost96
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.stdout.write(f'Found {len(rows)} Post-1996 counties')
        
        created_count = 0
        
        for row in rows:
            try:
                county_id = row.get('CountyPost96ID')
                county_name = row.get('CountyPost96')
                
                if not county_name:
                    continue
                
                if not dry_run:
                    county, created = Post1996County.objects.update_or_create(
                        id=county_id,
                        defaults={'name': county_name}
                    )
                    if created:
                        created_count += 1
                else:
                    self.stdout.write(f"Would create: {county_name} (ID: {county_id})")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing Post-1996 county {row.get('CountyPost96')}: {str(e)}")
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Post-1996 Counties: {created_count} created')
        )
    
    @transaction.atomic
    def migrate_regional_boards(self, cursor, dry_run=False):
        """Migrate Regional Boards from MSSQL"""
        self.stdout.write('Migrating Regional Boards...')
        
        query = "SELECT RegionalBoard1948ID, RegionalBoard1948 FROM dbo.tblRefRegionalBoard1948"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.stdout.write(f'Found {len(rows)} Regional Boards')
        
        created_count = 0
        
        for row in rows:
            try:
                board_id = row.get('RegionalBoard1948ID')
                board_name = row.get('RegionalBoard1948')
                
                if not board_name:
                    continue
                
                if not dry_run:
                    board, created = RegionalBoard.objects.update_or_create(
                        id=board_id,
                        defaults={'name': board_name}
                    )
                    if created:
                        created_count += 1
                else:
                    self.stdout.write(f"Would create: {board_name} (ID: {board_id})")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing Regional Board {row.get('RegionalBoard1948')}: {str(e)}")
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Regional Boards: {created_count} created')
        )
    
    @transaction.atomic
    def migrate_management_committees(self, cursor, dry_run=False):
        """Migrate Management Committees from MSSQL"""
        self.stdout.write('Migrating Management Committees...')
        
        query = "SELECT ManagementCommittee1948ID, ManagementCommittee1948 FROM dbo.tblRefManagementCommittee1948"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.stdout.write(f'Found {len(rows)} Management Committees')
        
        created_count = 0
        
        for row in rows:
            try:
                committee_id = row.get('ManagementCommittee1948ID')
                committee_name = row.get('ManagementCommittee1948')
                
                if not committee_name:
                    continue
                
                if not dry_run:
                    committee, created = ManagementCommittee.objects.update_or_create(
                        id=committee_id,
                        defaults={'name': committee_name}
                    )
                    if created:
                        created_count += 1
                else:
                    self.stdout.write(f"Would create: {committee_name} (ID: {committee_id})")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing Management Committee {row.get('ManagementCommittee1948')}: {str(e)}")
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Management Committees: {created_count} created')
        )
    
    @transaction.atomic
    def migrate_pre_1982_regional_authorities(self, cursor, dry_run=False):
        """Migrate Pre-1982 Regional Authorities from MSSQL"""
        self.stdout.write('Migrating Pre-1982 Regional Authorities...')
        
        query = "SELECT RegionalAuthority1974ID, RegionalAuthority1974 FROM dbo.tblRefRegionalAuthority1974"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.stdout.write(f'Found {len(rows)} Pre-1982 Regional Authorities')
        
        created_count = 0
        
        for row in rows:
            try:
                authority_id = row.get('RegionalAuthority1974ID')
                authority_name = row.get('RegionalAuthority1974')
                
                if not authority_name:
                    continue
                
                if not dry_run:
                    authority, created = Pre1982RegionalAuthority.objects.update_or_create(
                        id=authority_id,
                        defaults={'name': authority_name}
                    )
                    if created:
                        created_count += 1
                else:
                    self.stdout.write(f"Would create: {authority_name} (ID: {authority_id})")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing Pre-1982 Regional Authority {row.get('RegionalAuthority1974')}: {str(e)}")
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Pre-1982 Regional Authorities: {created_count} created')
        )
    
    @transaction.atomic
    def migrate_post_1982_regional_authorities(self, cursor, dry_run=False):
        """Migrate Post-1982 Regional Authorities from MSSQL"""
        self.stdout.write('Migrating Post-1982 Regional Authorities...')
        
        query = "SELECT RegionalAuthority1982ID, RegionalAuthority1982 FROM dbo.tblRefRegionalAuthority1982"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.stdout.write(f'Found {len(rows)} Post-1982 Regional Authorities')
        
        created_count = 0
        
        for row in rows:
            try:
                authority_id = row.get('RegionalAuthority1982ID')
                authority_name = row.get('RegionalAuthority1982')
                
                if not authority_name:
                    continue
                
                if not dry_run:
                    authority, created = Post1982RegionalAuthority.objects.update_or_create(
                        id=authority_id,
                        defaults={'name': authority_name}
                    )
                    if created:
                        created_count += 1
                else:
                    self.stdout.write(f"Would create: {authority_name} (ID: {authority_id})")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing Post-1982 Regional Authority {row.get('RegionalAuthority1982')}: {str(e)}")
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Post-1982 Regional Authorities: {created_count} created')
        )
    
    @transaction.atomic
    def migrate_pre_1982_district_authorities(self, cursor, dry_run=False):
        """Migrate Pre-1982 District Authorities from MSSQL"""
        self.stdout.write('Migrating Pre-1982 District Authorities...')
        
        query = "SELECT DistrictAuthority1974ID, DistrictAuthority1974 FROM dbo.tblRefDistrictAuthority1974"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.stdout.write(f'Found {len(rows)} Pre-1982 District Authorities')
        
        created_count = 0
        
        for row in rows:
            try:
                authority_id = row.get('DistrictAuthority1974ID')
                authority_name = row.get('DistrictAuthority1974')
                
                if not authority_name:
                    continue
                
                if not dry_run:
                    authority, created = Pre1982DistrictAuthority.objects.update_or_create(
                        id=authority_id,
                        defaults={'name': authority_name}
                    )
                    if created:
                        created_count += 1
                else:
                    self.stdout.write(f"Would create: {authority_name} (ID: {authority_id})")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing Pre-1982 District Authority {row.get('DistrictAuthority1974')}: {str(e)}")
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Pre-1982 District Authorities: {created_count} created')
        )
    
    @transaction.atomic
    def migrate_post_1982_district_authorities(self, cursor, dry_run=False):
        """Migrate Post-1982 District Authorities from MSSQL"""
        self.stdout.write('Migrating Post-1982 District Authorities...')
        
        query = "SELECT DistrictAuthority1982ID, DistrictAuthority1982 FROM dbo.tblRefDistrictAuthority1982"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.stdout.write(f'Found {len(rows)} Post-1982 District Authorities')
        
        created_count = 0
        
        for row in rows:
            try:
                authority_id = row.get('DistrictAuthority1982ID')
                authority_name = row.get('DistrictAuthority1982')
                
                if not authority_name:
                    continue
                
                if not dry_run:
                    authority, created = Post1982DistrictAuthority.objects.update_or_create(
                        id=authority_id,
                        defaults={'name': authority_name}
                    )
                    if created:
                        created_count += 1
                else:
                    self.stdout.write(f"Would create: {authority_name} (ID: {authority_id})")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing Post-1982 District Authority {row.get('DistrictAuthority1982')}: {str(e)}")
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Post-1982 District Authorities: {created_count} created')
        )
    
    @transaction.atomic
    def migrate_hospitals(self, cursor, dry_run=False):
        """
        Migrate hospital records from MSSQL to Postgres.
        Adjust table name and field mappings according to your MSSQL schema.
        """
        self.stdout.write('Migrating hospitals...')
        
        query = """
            SELECT 
                [Hospital_No]
                ,[PresentName]
                ,[PresentNameDate]
                ,[PreviousNames]
                ,[Street1]
                ,[Street2]
                ,[Town]
                ,[PostCode]
                ,[AddressFrom]
                ,[PreviousLocations]
                ,[PresentTrust]
                ,[PresentTrustDate]
                ,[PreviousTrusts]
                ,[FoundationDate]
                ,[FoundationDateApproximate]
                ,[Closed]
                ,[ClosureDate]
                ,[ClosureDateApproximate]
                ,[Pre1948Voluntary]
                ,[Pre1948PoorLaw]
                ,[Pre1948LocalAuthority]
                ,[Pre1948Private]
                ,[Pre1948OtherStatus]
                ,[Pre1948StatusInfo]
                ,[Post1948NHS]
                ,[Post1948Private]
                ,[Post1948Trust]
                ,[Post1948OtherStatus]
                ,[Post1948StatusInfo]
                ,[Pre1948General]
                ,[Pre1948Isolation]
                ,[Pre1948Maternity]
                ,[Pre1948Mental]
                ,[Pre1948Tuberculosis]
                ,[Pre1948Women]
                ,[Pre1948Children]
                ,[Pre1948Military]
                ,[Pre1948OtherType]
                ,[Pre1948TypeInfo]
                ,[Post1948Acute]
                ,[Post1948Geriatric]
                ,[Post1948Maternity]
                ,[Post1948Mental]
                ,[Post1948Hospice]
                ,[Post1948Military]
                ,[Post1948OtherType]
                ,[Post1948TypeInfo]
                ,[OtherInfoHistory]
                ,[MoreResearchReqd]
                ,[ResearcherInstruction]
                ,[InputDate]
                ,[LastUpdatedDate]
                ,[CountyPre74ID]
                ,[CountyPost74ID]
                ,[CountyPost96ID]
                ,[RegionalBoard1948ID]
                ,[ManagementCommittee1948ID]
                ,[RegionalAuthority1974ID]
                ,[DistrictAuthority1974ID]
                ,[RegionalAuthority1982ID]
                ,[DistrictAuthority1982ID]
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
                
                if not dry_run:
                    # Use update_or_create to handle duplicates
                    hospital, created = Hospital.objects.update_or_create(
                        name=hospital_data['name'],
                        defaults=hospital_data
                    )
                    
                    # Handle Pre-1948 Status many-to-many relationships
                    hospital.pre_1948_status.clear()
                    if row.get('Pre1948Voluntary'):
                        status = Pre1948Status.objects.get(value='Voluntary')
                        hospital.pre_1948_status.add(status)
                    if row.get('Pre1948PoorLaw'):
                        status = Pre1948Status.objects.get(value='Poor Law')
                        hospital.pre_1948_status.add(status)
                    if row.get('Pre1948LocalAuthority'):
                        status = Pre1948Status.objects.get(value='Local Authority')
                        hospital.pre_1948_status.add(status)
                    if row.get('Pre1948Private'):
                        status = Pre1948Status.objects.get(value='Private')
                        hospital.pre_1948_status.add(status)
                    if row.get('Pre1948OtherStatus'):
                        status = Pre1948Status.objects.get(value='Other')
                        hospital.pre_1948_status.add(status)
                    
                    # Handle Post-1948 Status many-to-many relationships
                    hospital.post_1948_status.clear()
                    if row.get('Post1948NHS'):
                        status = Post1948Status.objects.get(value='NHS')
                        hospital.post_1948_status.add(status)
                    if row.get('Post1948Private'):
                        status = Post1948Status.objects.get(value='Private')
                        hospital.post_1948_status.add(status)
                    if row.get('Post1948Trust'):
                        status = Post1948Status.objects.get(value='Trust')
                        hospital.post_1948_status.add(status)
                    if row.get('Post1948OtherStatus'):
                        status = Post1948Status.objects.get(value='Other')
                        hospital.post_1948_status.add(status)
                    
                    # Handle Pre-1948 Type many-to-many relationships
                    hospital.pre_1948_type.clear()
                    if row.get('Pre1948General'):
                        type_obj = Pre1948Type.objects.get(value='General')
                        hospital.pre_1948_type.add(type_obj)
                    if row.get('Pre1948Isolation'):
                        type_obj = Pre1948Type.objects.get(value='Isolation')
                        hospital.pre_1948_type.add(type_obj)
                    if row.get('Pre1948Maternity'):
                        type_obj = Pre1948Type.objects.get(value='Maternity')
                        hospital.pre_1948_type.add(type_obj)
                    if row.get('Pre1948Mental'):
                        type_obj = Pre1948Type.objects.get(value='Mental')
                        hospital.pre_1948_type.add(type_obj)
                    if row.get('Pre1948Tuberculosis'):
                        type_obj = Pre1948Type.objects.get(value='Tuberculosis')
                        hospital.pre_1948_type.add(type_obj)
                    if row.get('Pre1948Women'):
                        type_obj = Pre1948Type.objects.get(value='Women')
                        hospital.pre_1948_type.add(type_obj)
                    if row.get('Pre1948Children'):
                        type_obj = Pre1948Type.objects.get(value='Children')
                        hospital.pre_1948_type.add(type_obj)
                    if row.get('Pre1948Military'):
                        type_obj = Pre1948Type.objects.get(value='Military')
                        hospital.pre_1948_type.add(type_obj)
                    if row.get('Pre1948OtherType'):
                        type_obj = Pre1948Type.objects.get(value='Other')
                        hospital.pre_1948_type.add(type_obj)
                    
                    # Handle Post-1948 Type many-to-many relationships
                    hospital.post_1948_type.clear()
                    if row.get('Post1948Acute'):
                        type_obj = Post1948Type.objects.get(value='Acute')
                        hospital.post_1948_type.add(type_obj)
                    if row.get('Post1948Geriatric'):
                        type_obj = Post1948Type.objects.get(value='Geriatric')
                        hospital.post_1948_type.add(type_obj)
                    if row.get('Post1948Maternity'):
                        type_obj = Post1948Type.objects.get(value='Maternity')
                        hospital.post_1948_type.add(type_obj)
                    if row.get('Post1948Mental'):
                        type_obj = Post1948Type.objects.get(value='Mental')
                        hospital.post_1948_type.add(type_obj)
                    if row.get('Post1948Hospice'):
                        type_obj = Post1948Type.objects.get(value='Hospice')
                        hospital.post_1948_type.add(type_obj)
                    if row.get('Post1948Military'):
                        type_obj = Post1948Type.objects.get(value='Military')
                        hospital.post_1948_type.add(type_obj)
                    if row.get('Post1948OtherType'):
                        type_obj = Post1948Type.objects.get(value='Other')
                        hospital.post_1948_type.add(type_obj)
                    
                    # Handle county foreign key relationships (skip if ID=1, set to None instead)
                    if fk_data.get('pre_1974_county_id') and fk_data['pre_1974_county_id'] != 1:
                        try:
                            if Pre1974County.objects.filter(id=fk_data['pre_1974_county_id']).exists():
                                hospital.pre_1974_county_id = fk_data['pre_1974_county_id']
                            else:
                                hospital.pre_1974_county_id = None
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f"Could not set Pre-1974 county for {hospital.name}: {str(e)}")
                            )
                    else:
                        hospital.pre_1974_county_id = None
                    
                    if fk_data.get('post_1974_county_id') and fk_data['post_1974_county_id'] != 1:
                        try:
                            if Post1974County.objects.filter(id=fk_data['post_1974_county_id']).exists():
                                hospital.post_1974_county_id = fk_data['post_1974_county_id']
                            else:
                                hospital.post_1974_county_id = None
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f"Could not set Post-1974 county for {hospital.name}: {str(e)}")
                            )
                    else:
                        hospital.post_1974_county_id = None
                    
                    if fk_data.get('post_1996_county_id') and fk_data['post_1996_county_id'] != 1:
                        try:
                            if Post1996County.objects.filter(id=fk_data['post_1996_county_id']).exists():
                                hospital.post_1996_county_id = fk_data['post_1996_county_id']
                            else:
                                hospital.post_1996_county_id = None
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f"Could not set Post-1996 county for {hospital.name}: {str(e)}")
                            )
                    else:
                        hospital.post_1996_county_id = None
                    
                    # Handle authority foreign key relationships (skip if ID=1, set to None instead)
                    if fk_data.get('regional_board_id') and fk_data['regional_board_id'] != 1:
                        try:
                            if RegionalBoard.objects.filter(id=fk_data['regional_board_id']).exists():
                                hospital.regional_board_id = fk_data['regional_board_id']
                            else:
                                hospital.regional_board_id = None
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f"Could not set Regional Board for {hospital.name}: {str(e)}")
                            )
                    else:
                        hospital.regional_board_id = None
                    
                    if fk_data.get('management_committee_id') and fk_data['management_committee_id'] != 1:
                        try:
                            if ManagementCommittee.objects.filter(id=fk_data['management_committee_id']).exists():
                                hospital.management_committee_id = fk_data['management_committee_id']
                            else:
                                hospital.management_committee_id = None
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f"Could not set Management Committee for {hospital.name}: {str(e)}")
                            )
                    else:
                        hospital.management_committee_id = None
                    
                    if fk_data.get('pre_1982_regional_authority_id') and fk_data['pre_1982_regional_authority_id'] != 1:
                        try:
                            if Pre1982RegionalAuthority.objects.filter(id=fk_data['pre_1982_regional_authority_id']).exists():
                                hospital.pre_1982_regional_authority_id = fk_data['pre_1982_regional_authority_id']
                            else:
                                hospital.pre_1982_regional_authority_id = None
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f"Could not set Pre-1982 Regional Authority for {hospital.name}: {str(e)}")
                            )
                    else:
                        hospital.pre_1982_regional_authority_id = None
                    
                    if fk_data.get('post_1982_regional_authority_id') and fk_data['post_1982_regional_authority_id'] != 1:
                        try:
                            if Post1982RegionalAuthority.objects.filter(id=fk_data['post_1982_regional_authority_id']).exists():
                                hospital.post_1982_regional_authority_id = fk_data['post_1982_regional_authority_id']
                            else:
                                hospital.post_1982_regional_authority_id = None
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f"Could not set Post-1982 Regional Authority for {hospital.name}: {str(e)}")
                            )
                    else:
                        hospital.post_1982_regional_authority_id = None
                    
                    if fk_data.get('pre_1982_district_authority_id') and fk_data['pre_1982_district_authority_id'] != 1:
                        try:
                            if Pre1982DistrictAuthority.objects.filter(id=fk_data['pre_1982_district_authority_id']).exists():
                                hospital.pre_1982_district_authority_id = fk_data['pre_1982_district_authority_id']
                            else:
                                hospital.pre_1982_district_authority_id = None
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f"Could not set Pre-1982 District Authority for {hospital.name}: {str(e)}")
                            )
                    else:
                        hospital.pre_1982_district_authority_id = None
                    
                    if fk_data.get('post_1982_district_authority_id') and fk_data['post_1982_district_authority_id'] != 1:
                        try:
                            if Post1982DistrictAuthority.objects.filter(id=fk_data['post_1982_district_authority_id']).exists():
                                hospital.post_1982_district_authority_id = fk_data['post_1982_district_authority_id']
                            else:
                                hospital.post_1982_district_authority_id = None
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f"Could not set Post-1982 District Authority for {hospital.name}: {str(e)}")
                            )
                    else:
                        hospital.post_1982_district_authority_id = None
                    
                    hospital.save()
                    
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
    
    # Add more migration methods for other models
    # Example template:
    # @transaction.atomic
    # def migrate_records_info(self, cursor, dry_run=False):
    #     self.stdout.write('Migrating records info...')
    #     query = "SELECT * FROM records_info_table"
    #     cursor.execute(query)
    #     rows = cursor.fetchall()
    #     # Process rows...
