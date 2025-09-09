"""
OLIS Synchronization Service
Handles fetching data from Oregon Legislature API and storing it in PostgreSQL database
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from database_config import AsyncSessionLocal
from database.models_with_analysis import (
    LegislativeSession, Committee, Measure, MeasureSponsor, 
    Company, User, Testimony, Legislator, MeasureVote, 
    CommitteeVote, CommitteeMember, MeasureHistoryAction,
    CommitteeMeeting, CommitteeAgendaItem, MeasureDocument,
    CommitteeMeetingDocument, CommitteeProposedAmendment,
    FloorSessionAgendaItem, FloorLetter
)
from olis_client import OLISClient
import uuid

# Set up logging
logger = logging.getLogger(__name__)

class OLISSyncService:
    """
    Service for synchronizing data from OLIS API to PostgreSQL database
    """
    
    def __init__(self):
        self.client = OLISClient()
        self.sync_stats = {
            'sessions_processed': 0,
            'measures_processed': 0,
            'committees_processed': 0,
            'testimonies_processed': 0,
            'legislators_processed': 0,
            'measure_votes_processed': 0,
            'committee_votes_processed': 0,
            'committee_members_processed': 0,
            'history_actions_processed': 0,
            'committee_meetings_processed': 0,
            'agenda_items_processed': 0,
            'measure_documents_processed': 0,
            'meeting_documents_processed': 0,
            'measure_sponsors_processed': 0,
            'committee_proposed_amendments_processed': 0,
            'floor_session_agenda_items_processed': 0,
            'floor_letters_processed': 0,
            'errors': [],
            'start_time': None,
            'end_time': None
        }
    
    async def sync_session_data(self, session_key: str = None) -> Dict[str, Any]:
        """
        Main synchronization method - syncs all data for a session or all sessions
        
        Args:
            session_key: Specific session to sync, or None for all sessions
            
        Returns:
            Dictionary with sync results and statistics
        """
        self.sync_stats['start_time'] = datetime.now()
        logger.info(f"Starting OLIS sync for session: {session_key or 'ALL'}")
        
        try:
            async with AsyncSessionLocal() as db_session:
                # Step 1: Sync legislative sessions
                await self._sync_legislative_sessions(db_session, session_key)
                
                # Step 2: Get target sessions to sync
                target_sessions = []
                if session_key:
                    # Sync specific session
                    target_sessions = [session_key]
                else:
                    # Get all available sessions
                    sessions = await self.client.get_sessions()
                    target_sessions = [s['SessionKey'] for s in sessions]  # Process all available sessions
                
                # Step 3: Sync each session's data
                for sess_key in target_sessions:
                    logger.info(f"Syncing session: {sess_key}")
                    
                    # Sync committees for this session
                    await self._sync_committees(db_session, sess_key)
                    
                    # Sync measures for this session
                    await self._sync_measures(db_session, sess_key)
                    
                    # PHASE 1: Sync legislators and voting data
                    await self._sync_legislators(db_session, sess_key)
                    await self._sync_committee_members(db_session, sess_key)
                    await self._sync_measure_history_actions(db_session, sess_key)
                    await self._sync_measure_votes(db_session, sess_key)
                    await self._sync_committee_votes(db_session, sess_key)
                    
                    # PHASE 2: Sync meetings and documents
                    await self.sync_committee_meetings(db_session, session)
                    await self.sync_agenda_items(db_session, session)
                    await self.sync_measure_documents(db_session, session)
                    await self.sync_committee_meeting_documents(db_session, session)
                    
                    # PHASE 3: Sync sponsors and administrative data
                    await self.sync_measure_sponsors(db_session, session)
                    await self.sync_committee_proposed_amendments(db_session, session)
                    await self.sync_floor_session_agenda_items(db_session, session)
                    await self.sync_floor_letters(db_session, session)
                    
                    self.sync_stats['sessions_processed'] += 1
                
                # Commit all changes
                await db_session.commit()
                
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            self.sync_stats['errors'].append(str(e))
            raise
        
        finally:
            self.sync_stats['end_time'] = datetime.now()
            duration = self.sync_stats['end_time'] - self.sync_stats['start_time']
            logger.info(f"Sync completed in {duration.total_seconds():.2f} seconds")
        
        return self.sync_stats
    
    async def _sync_legislative_sessions(self, db_session: AsyncSession, target_session_key: str = None):
        """Sync legislative session data"""
        if target_session_key:
            logger.info(f"Syncing specific legislative session: {target_session_key}")
        else:
            logger.info("Syncing all legislative sessions...")
        
        try:
            sessions = await self.client.get_sessions()
            
            # Filter to target session if specified
            if target_session_key:
                sessions = [s for s in sessions if s['SessionKey'] == target_session_key]
                if not sessions:
                    logger.warning(f"Target session {target_session_key} not found in OLIS")
                    return
            
            for session_data in sessions:
                # Check if session already exists
                stmt = select(LegislativeSession).where(
                    LegislativeSession.session_key == session_data['SessionKey']
                )
                existing = await db_session.execute(stmt)
                session = existing.scalar_one_or_none()
                
                if not session:
                    # Create new session
                    session = LegislativeSession(
                        session_key=session_data['SessionKey'],
                        session_name=session_data.get('SessionName', session_data['SessionKey']),
                        session_year=int(session_data['SessionKey'][:4]) if session_data['SessionKey'][:4].isdigit() else 2025,
                        is_current=session_data.get('IsCurrent', False),
                        begin_date=None,  # OLIS doesn't provide this directly
                        end_date=None     # OLIS doesn't provide this directly
                    )
                    db_session.add(session)
                    logger.info(f"Added session: {session_data['SessionKey']}")
                else:
                    # Update existing session
                    session.session_name = session_data.get('SessionName', session_data['SessionKey'])
                    session.is_current = session_data.get('IsCurrent', False)
                    logger.info(f"Updated session: {session_data['SessionKey']}")
            
            await db_session.flush()
            
        except Exception as e:
            logger.error(f"Failed to sync sessions: {str(e)}")
            raise
    
    async def _sync_committees(self, db_session: AsyncSession, session_key: str):
        """Sync committee data for a session"""
        logger.info(f"Syncing committees for session: {session_key}")
        
        try:
            # Get session ID
            stmt = select(LegislativeSession).where(
                LegislativeSession.session_key == session_key
            )
            result = await db_session.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                logger.warning(f"Session {session_key} not found in database")
                return
            
            # Get measures to extract committee information
            measures = await self.client.get_all_measures(session_key)
            
            # Extract unique committees from measures
            committees_seen = set()
            
            for measure in measures:  # Process all measures to extract committees
                committee_code = measure.get('CurrentCommitteeCode')
                if committee_code and committee_code not in committees_seen:
                    committees_seen.add(committee_code)
                    
                    # Check if committee exists
                    stmt = select(Committee).where(
                        Committee.session_id == session.id,
                        Committee.committee_code == committee_code
                    )
                    existing = await db_session.execute(stmt)
                    committee = existing.scalar_one_or_none()
                    
                    if not committee:
                        # Create new committee
                        committee = Committee(
                            session_id=session.id,
                            committee_code=committee_code,
                            committee_name=f"Committee {committee_code}",  # Basic name
                            chamber=committee_code[0] if committee_code else 'U',  # H/S/J
                            is_active=True
                        )
                        db_session.add(committee)
                        self.sync_stats['committees_processed'] += 1
                        logger.info(f"Added committee: {committee_code}")
            
            await db_session.flush()
            
        except Exception as e:
            logger.error(f"Failed to sync committees: {str(e)}")
            self.sync_stats['errors'].append(f"Committees sync error: {str(e)}")
    
    async def _sync_measures(self, db_session: AsyncSession, session_key: str):
        """Sync measure data for a session"""
        logger.info(f"Syncing measures for session: {session_key}")
        
        try:
            # Get session
            stmt = select(LegislativeSession).where(
                LegislativeSession.session_key == session_key
            )
            result = await db_session.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                logger.warning(f"Session {session_key} not found")
                return
            
            # Get measures from OLIS
            measures = await self.client.get_all_measures(session_key)
            logger.info(f"Found {len(measures)} measures for session {session_key}")
            
            # Get all existing measures for this session in one query
            existing_measures_stmt = select(Measure).where(Measure.session_id == session.id)
            existing_result = await db_session.execute(existing_measures_stmt)
            existing_measures = {
                (m.measure_prefix, m.measure_number): m 
                for m in existing_result.scalars().all()
            }
            logger.info(f"Found {len(existing_measures)} existing measures in database")
            
            # Process all measures for complete synchronization
            measures_to_process = measures
            logger.info(f"Processing {len(measures_to_process)} measures")
            
            # Process measures in batches for better performance
            batch_size = 500  # Increased batch size since we removed individual queries
            new_measures = []
            
            for i, measure_data in enumerate(measures_to_process):
                try:
                    measure_prefix = measure_data.get('MeasurePrefix', '')
                    measure_number = self._safe_int(measure_data.get('MeasureNumber')) or 0
                    measure_key = (measure_prefix, measure_number)
                    
                    if measure_key in existing_measures:
                        # Update existing measure
                        measure = existing_measures[measure_key]
                        measure.measure_summary = measure_data.get('MeasureSummary') or measure.measure_summary
                        measure.current_location = measure_data.get('CurrentLocation') or measure.current_location
                        measure.current_committee_code = measure_data.get('CurrentCommitteeCode') or measure.current_committee_code
                        measure.modified_date = self._parse_date(measure_data.get('ModifiedDate')) or measure.modified_date
                        
                        # Update integer fields with proper conversion (handle OLIS placeholders)
                        lc_number_raw = measure_data.get('LCNumber')
                        if lc_number_raw:
                            if lc_number_raw == '9999' or lc_number_raw == 9999:
                                measure.lc_number = None
                            else:
                                measure.lc_number = self._safe_int(lc_number_raw)
                        
                        chapter_number_raw = measure_data.get('ChapterNumber')
                        if chapter_number_raw:
                            if chapter_number_raw == '9999' or chapter_number_raw == 9999:
                                measure.chapter_number = None
                            else:
                                measure.chapter_number = self._safe_int(chapter_number_raw)
                        
                        measure.last_synced_at = datetime.now()
                    else:
                        # Create new measure
                        new_measure = self._create_measure_from_data(session, measure_data)
                        new_measures.append(new_measure)
                    
                    self.sync_stats['measures_processed'] += 1
                    
                    # Batch processing - flush every batch_size measures
                    if (i + 1) % batch_size == 0 or i == len(measures_to_process) - 1:
                        if new_measures:
                            db_session.add_all(new_measures)
                            logger.info(f"Added {len(new_measures)} new measures to batch")
                            new_measures = []
                        
                        await db_session.flush()
                        logger.info(f"Processed {i + 1}/{len(measures_to_process)} measures")
                        
                except Exception as e:
                    logger.error(f"Failed to process measure {measure_data.get('MeasureNumber', 'Unknown')}: {str(e)}")
                    self.sync_stats['errors'].append(f"Measure {measure_data.get('MeasureNumber', 'Unknown')}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to sync measures: {str(e)}")
            self.sync_stats['errors'].append(f"Measures sync error: {str(e)}")
    
    def _create_measure_from_data(self, session: LegislativeSession, measure_data: Dict[str, Any]) -> Measure:
        """Create a new Measure object from OLIS data"""
        measure_prefix = measure_data.get('MeasurePrefix', '')
        measure_number = self._safe_int(measure_data.get('MeasureNumber')) or 0
        
        # Explicitly convert integer fields to handle OLIS placeholder values
        lc_number_raw = measure_data.get('LCNumber')
        chapter_number_raw = measure_data.get('ChapterNumber')
        
        # Convert LCNumber - treat '9999' as None (OLIS placeholder)
        if lc_number_raw == '9999' or lc_number_raw == 9999:
            lc_number = None
        else:
            lc_number = self._safe_int(lc_number_raw)
            
        # Convert ChapterNumber - treat '9999' as None (OLIS placeholder)
        if chapter_number_raw == '9999' or chapter_number_raw == 9999:
            chapter_number = None
        else:
            chapter_number = self._safe_int(chapter_number_raw)
        
        return Measure(
            session_id=session.id,
            session_key=session.session_key,
            measure_prefix=measure_prefix,
            measure_number=measure_number,
            prefix_meaning=measure_data.get('PrefixMeaning'),
            lc_number=lc_number,
            chapter_number=chapter_number,
            measure_summary=measure_data.get('MeasureSummary'),
            catch_line=measure_data.get('CatchLine'),
            minority_catch_line=measure_data.get('MinorityCatchLine'),
            relating_to=measure_data.get('RelatingTo'),
            relating_to_full=measure_data.get('RelatingToFull'),
            at_the_request_of=measure_data.get('AtTheRequestOf'),
            current_location=measure_data.get('CurrentLocation'),
            current_version=measure_data.get('CurrentVersion'),
            current_committee_code=measure_data.get('CurrentCommitteeCode'),
            current_subcommittee=measure_data.get('CurrentSubcommittee'),
            created_date=self._parse_date(measure_data.get('CreatedDate')),
            modified_date=self._parse_date(measure_data.get('ModifiedDate')),
            effective_date=self._parse_date(measure_data.get('EffectiveDate')),
            fiscal_impact=measure_data.get('FiscalImpact'),
            revenue_impact=measure_data.get('RevenueImpact'),
            fiscal_analyst=measure_data.get('FiscalAnalyst'),
            revenue_economist=measure_data.get('RevenueEconomist'),
            emergency_clause=measure_data.get('EmergencyClause', False),
            vetoed=measure_data.get('Vetoed', False),
            chamber=self._determine_chamber(measure_prefix),
            bill_type=self._determine_bill_type(measure_prefix),
            status_category='active',
            priority_score=0,
            sync_status='synced',
            last_synced_at=datetime.now()
        )
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert a value to integer, handling None and invalid strings"""
        if value is None or value == '':
            return None
        
        try:
            # Handle numeric strings
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return None
                return int(value)
            # Handle numeric values
            elif isinstance(value, (int, float)):
                return int(value)
            else:
                return None
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse date string from OLIS API"""
        if not date_string:
            return None
        
        try:
            # OLIS uses various date formats, try common ones
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%m/%d/%Y']:
                try:
                    return datetime.strptime(date_string.split('.')[0], fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None
    
    def _determine_chamber(self, prefix: str) -> str:
        """Determine chamber from measure prefix"""
        if not prefix:
            return 'Unknown'
        
        prefix_upper = prefix.upper()
        if prefix_upper.startswith('H'):
            return 'House'
        elif prefix_upper.startswith('S'):
            return 'Senate'
        elif prefix_upper.startswith('J'):
            return 'Joint'
        else:
            return 'Unknown'
    
    def _determine_bill_type(self, prefix: str) -> str:
        """Determine bill type from measure prefix"""
        if not prefix:
            return 'Unknown'
        
        prefix_upper = prefix.upper()
        if 'B' in prefix_upper:
            return 'Bill'
        elif 'R' in prefix_upper:
            return 'Resolution'
        elif 'M' in prefix_upper:
            return 'Memorial'
        else:
            return 'Other'
    
    # =========================================================================
    # PHASE 1: LEGISLATORS & VOTING SYNC METHODS
    # =========================================================================
    
    async def _sync_legislators(self, db_session: AsyncSession, session_key: str):
        """Sync legislator data for a session"""
        logger.info(f"Syncing legislators for session: {session_key}")
        
        try:
            # Get session
            stmt = select(LegislativeSession).where(
                LegislativeSession.session_key == session_key
            )
            result = await db_session.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                logger.warning(f"Session {session_key} not found")
                return
            
            # Get legislators from OLIS
            legislators_data = await self.client.get_all_legislators(session_key)
            logger.info(f"Found {len(legislators_data)} legislators for session {session_key}")
            
            # Get existing legislators for this session
            existing_stmt = select(Legislator).where(Legislator.session_id == session.id)
            existing_result = await db_session.execute(existing_stmt)
            existing_legislators = {
                l.legislator_code: l for l in existing_result.scalars().all()
            }
            
            new_legislators = []
            for legislator_data in legislators_data:
                try:
                    legislator_code = legislator_data.get('LegislatorCode', '')
                    
                    if legislator_code in existing_legislators:
                        # Update existing legislator
                        legislator = existing_legislators[legislator_code]
                        legislator.first_name = legislator_data.get('FirstName', '')
                        legislator.last_name = legislator_data.get('LastName', '')
                        legislator.title = legislator_data.get('Title')
                        legislator.chamber = legislator_data.get('Chamber')
                        legislator.party = legislator_data.get('Party')
                        legislator.district_number = legislator_data.get('DistrictNumber')
                        legislator.capitol_address = legislator_data.get('CapitolAddress')
                        legislator.capitol_phone = legislator_data.get('CapitolPhone')
                        legislator.email_address = legislator_data.get('EmailAddress')
                        legislator.website_url = legislator_data.get('WebSiteUrl')
                        legislator.olis_modified_date = self._parse_date(legislator_data.get('ModifiedDate'))
                        legislator.last_synced_at = datetime.now()
                    else:
                        # Create new legislator
                        new_legislator = Legislator(
                            session_id=session.id,
                            session_key=session_key,
                            legislator_code=legislator_code,
                            first_name=legislator_data.get('FirstName', ''),
                            last_name=legislator_data.get('LastName', ''),
                            title=legislator_data.get('Title'),
                            chamber=legislator_data.get('Chamber'),
                            party=legislator_data.get('Party'),
                            district_number=legislator_data.get('DistrictNumber'),
                            capitol_address=legislator_data.get('CapitolAddress'),
                            capitol_phone=legislator_data.get('CapitolPhone'),
                            email_address=legislator_data.get('EmailAddress'),
                            website_url=legislator_data.get('WebSiteUrl'),
                            olis_created_date=self._parse_date(legislator_data.get('CreatedDate')),
                            olis_modified_date=self._parse_date(legislator_data.get('ModifiedDate'))
                        )
                        new_legislators.append(new_legislator)
                    
                    self.sync_stats['legislators_processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process legislator {legislator_data.get('LegislatorCode', 'Unknown')}: {str(e)}")
                    self.sync_stats['errors'].append(f"Legislator {legislator_data.get('LegislatorCode', 'Unknown')}: {str(e)}")
                    continue
            
            if new_legislators:
                db_session.add_all(new_legislators)
                logger.info(f"Added {len(new_legislators)} new legislators")
            
            await db_session.flush()
            
        except Exception as e:
            logger.error(f"Failed to sync legislators: {str(e)}")
            self.sync_stats['errors'].append(f"Legislators sync error: {str(e)}")
    
    async def _sync_committee_members(self, db_session: AsyncSession, session_key: str):
        """Sync committee members for a session"""
        logger.info(f"Syncing committee members for session: {session_key}")
        
        try:
            # Get session
            stmt = select(LegislativeSession).where(
                LegislativeSession.session_key == session_key
            )
            result = await db_session.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                logger.warning(f"Session {session_key} not found")
                return
            
            # Get committee members from OLIS
            members_data = await self.client.get_all_committee_members(session_key)
            logger.info(f"Found {len(members_data)} committee members for session {session_key}")
            
            # Get existing committee members for this session
            existing_stmt = select(CommitteeMember).where(CommitteeMember.session_id == session.id)
            existing_result = await db_session.execute(existing_stmt)
            existing_members = {
                f"{m.committee_code}_{m.legislator_code}": m 
                for m in existing_result.scalars().all()
            }
            
            # Get legislators and committees for foreign key lookups
            legislators_stmt = select(Legislator).where(Legislator.session_id == session.id)
            legislators_result = await db_session.execute(legislators_stmt)
            legislators_map = {l.legislator_code: l for l in legislators_result.scalars().all()}
            
            committees_stmt = select(Committee).where(Committee.session_id == session.id)
            committees_result = await db_session.execute(committees_stmt)
            committees_map = {c.committee_code: c for c in committees_result.scalars().all()}
            
            new_members = []
            for member_data in members_data:
                try:
                    committee_code = member_data.get('CommitteeCode', '')
                    legislator_code = member_data.get('LegislatorCode', '')
                    member_key = f"{committee_code}_{legislator_code}"
                    
                    if member_key in existing_members:
                        # Update existing member
                        member = existing_members[member_key]
                        member.title = member_data.get('Title')
                        member.olis_modified_date = self._parse_date(member_data.get('ModifiedDate'))
                        member.last_synced_at = datetime.now()
                    else:
                        # Create new member if both committee and legislator exist
                        committee = committees_map.get(committee_code)
                        legislator = legislators_map.get(legislator_code)
                        
                        if committee and legislator:
                            new_member = CommitteeMember(
                                session_id=session.id,
                                committee_id=committee.id,
                                legislator_id=legislator.id,
                                session_key=session_key,
                                committee_code=committee_code,
                                legislator_code=legislator_code,
                                title=member_data.get('Title'),
                                olis_created_date=self._parse_date(member_data.get('CreatedDate')),
                                olis_modified_date=self._parse_date(member_data.get('ModifiedDate'))
                            )
                            new_members.append(new_member)
                    
                    self.sync_stats['committee_members_processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process committee member {committee_code}_{legislator_code}: {str(e)}")
                    self.sync_stats['errors'].append(f"Committee member {committee_code}_{legislator_code}: {str(e)}")
                    continue
            
            if new_members:
                db_session.add_all(new_members)
                logger.info(f"Added {len(new_members)} new committee members")
            
            await db_session.flush()
            
        except Exception as e:
            logger.error(f"Failed to sync committee members: {str(e)}")
            self.sync_stats['errors'].append(f"Committee members sync error: {str(e)}")
    
    async def _sync_measure_history_actions(self, db_session: AsyncSession, session_key: str):
        """Sync measure history actions for a session"""
        logger.info(f"Syncing measure history actions for session: {session_key}")
        
        try:
            # Get session
            stmt = select(LegislativeSession).where(
                LegislativeSession.session_key == session_key
            )
            result = await db_session.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                logger.warning(f"Session {session_key} not found")
                return
            
            # Get history actions from OLIS
            actions_data = await self.client.get_all_measure_history_actions(session_key)
            logger.info(f"Found {len(actions_data)} history actions for session {session_key}")
            
            # Get existing actions for this session
            existing_stmt = select(MeasureHistoryAction).where(MeasureHistoryAction.session_id == session.id)
            existing_result = await db_session.execute(existing_stmt)
            existing_actions = {
                a.measure_history_id: a for a in existing_result.scalars().all()
            }
            
            # Get measures for foreign key lookups
            measures_stmt = select(Measure).where(Measure.session_id == session.id)
            measures_result = await db_session.execute(measures_stmt)
            measures_map = {
                (m.measure_prefix, m.measure_number): m 
                for m in measures_result.scalars().all()
            }
            
            new_actions = []
            batch_size = 500
            
            for i, action_data in enumerate(actions_data):
                try:
                    history_id = action_data.get('MeasureHistoryId')
                    measure_prefix = action_data.get('MeasurePrefix', '')
                    measure_number = self._safe_int(action_data.get('MeasureNumber')) or 0
                    measure_key = (measure_prefix, measure_number)
                    
                    if history_id in existing_actions:
                        # Update existing action
                        action = existing_actions[history_id]
                        action.action_text = action_data.get('ActionText', '')
                        action.vote_text = action_data.get('VoteText')
                        action.public_notification = action_data.get('PublicNotification', False)
                        action.olis_modified_date = self._parse_date(action_data.get('ModifiedDate'))
                        action.last_synced_at = datetime.now()
                    else:
                        # Create new action if measure exists
                        measure = measures_map.get(measure_key)
                        if measure:
                            new_action = MeasureHistoryAction(
                                session_id=session.id,
                                measure_id=measure.id,
                                measure_history_id=history_id,
                                session_key=session_key,
                                measure_prefix=measure_prefix,
                                measure_number=measure_number,
                                chamber=action_data.get('Chamber'),
                                action_date=self._parse_date(action_data.get('ActionDate')) or datetime.now(),
                                action_text=action_data.get('ActionText', ''),
                                vote_text=action_data.get('VoteText'),
                                public_notification=action_data.get('PublicNotification', False),
                                olis_created_date=self._parse_date(action_data.get('CreatedDate')) or datetime.now(),
                                olis_modified_date=self._parse_date(action_data.get('ModifiedDate'))
                            )
                            new_actions.append(new_action)
                    
                    self.sync_stats['history_actions_processed'] += 1
                    
                    # Batch processing
                    if (i + 1) % batch_size == 0 or i == len(actions_data) - 1:
                        if new_actions:
                            db_session.add_all(new_actions)
                            logger.info(f"Added {len(new_actions)} new history actions to batch")
                            new_actions = []
                        
                        await db_session.flush()
                        logger.info(f"Processed {i + 1}/{len(actions_data)} history actions")
                    
                except Exception as e:
                    logger.error(f"Failed to process history action {history_id}: {str(e)}")
                    self.sync_stats['errors'].append(f"History action {history_id}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to sync history actions: {str(e)}")
            self.sync_stats['errors'].append(f"History actions sync error: {str(e)}")
    
    async def _sync_measure_votes(self, db_session: AsyncSession, session_key: str):
        """Sync measure votes for a session"""
        logger.info(f"Syncing measure votes for session: {session_key}")
        
        try:
            # Get session
            stmt = select(LegislativeSession).where(
                LegislativeSession.session_key == session_key
            )
            result = await db_session.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                logger.warning(f"Session {session_key} not found")
                return
            
            # Get votes from OLIS
            votes_data = await self.client.get_all_measure_votes(session_key)
            logger.info(f"Found {len(votes_data)} measure votes for session {session_key}")
            
            if not votes_data:
                logger.info(f"No measure votes found for session {session_key}")
                return
            
            # Get existing votes for this session
            existing_stmt = select(MeasureVote).where(MeasureVote.session_id == session.id)
            existing_result = await db_session.execute(existing_stmt)
            existing_votes = {
                v.measure_vote_id: v for v in existing_result.scalars().all()
            }
            
            # Get measures and legislators for foreign key lookups
            measures_stmt = select(Measure).where(Measure.session_id == session.id)
            measures_result = await db_session.execute(measures_stmt)
            measures_map = {
                (m.measure_prefix, m.measure_number): m 
                for m in measures_result.scalars().all()
            }
            
            legislators_stmt = select(Legislator).where(Legislator.session_id == session.id)
            legislators_result = await db_session.execute(legislators_stmt)
            legislators_map = {l.legislator_code: l for l in legislators_result.scalars().all()}
            
            new_votes = []
            batch_size = 500
            
            for i, vote_data in enumerate(votes_data):
                try:
                    vote_id = vote_data.get('MeasureVoteId')
                    measure_prefix = vote_data.get('MeasurePrefix', '')
                    measure_number = self._safe_int(vote_data.get('MeasureNumber')) or 0
                    vote_name = vote_data.get('VoteName', '')
                    measure_key = (measure_prefix, measure_number)
                    
                    if vote_id in existing_votes:
                        # Update existing vote
                        vote = existing_votes[vote_id]
                        vote.vote = vote_data.get('Vote', '')
                        vote.action_text = vote_data.get('ActionText')
                        vote.olis_modified_date = self._parse_date(vote_data.get('ModifiedDate'))
                        vote.last_synced_at = datetime.now()
                    else:
                        # Create new vote if measure exists
                        measure = measures_map.get(measure_key)
                        # Try to find legislator by vote name
                        legislator = legislators_map.get(vote_name)
                        
                        if measure and legislator:
                            new_vote = MeasureVote(
                                session_id=session.id,
                                measure_id=measure.id,
                                legislator_id=legislator.id,
                                measure_vote_id=vote_id,
                                measure_history_id=vote_data.get('MeasureHistoryId'),
                                session_key=session_key,
                                measure_prefix=measure_prefix,
                                measure_number=measure_number,
                                vote=vote_data.get('Vote', ''),
                                vote_name=vote_name,
                                chamber=vote_data.get('Chamber'),
                                action_date=self._parse_date(vote_data.get('ActionDate')) or datetime.now(),
                                action_text=vote_data.get('ActionText'),
                                olis_created_date=self._parse_date(vote_data.get('CreatedDate')) or datetime.now(),
                                olis_modified_date=self._parse_date(vote_data.get('ModifiedDate'))
                            )
                            new_votes.append(new_vote)
                    
                    self.sync_stats['measure_votes_processed'] += 1
                    
                    # Batch processing
                    if (i + 1) % batch_size == 0 or i == len(votes_data) - 1:
                        if new_votes:
                            db_session.add_all(new_votes)
                            logger.info(f"Added {len(new_votes)} new measure votes to batch")
                            new_votes = []
                        
                        await db_session.flush()
                        logger.info(f"Processed {i + 1}/{len(votes_data)} measure votes")
                    
                except Exception as e:
                    logger.error(f"Failed to process measure vote {vote_id}: {str(e)}")
                    self.sync_stats['errors'].append(f"Measure vote {vote_id}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to sync measure votes: {str(e)}")
            self.sync_stats['errors'].append(f"Measure votes sync error: {str(e)}")
    
    async def _sync_committee_votes(self, db_session: AsyncSession, session_key: str):
        """Sync committee votes for a session"""
        logger.info(f"Syncing committee votes for session: {session_key}")
        
        try:
            # Get session
            stmt = select(LegislativeSession).where(
                LegislativeSession.session_key == session_key
            )
            result = await db_session.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                logger.warning(f"Session {session_key} not found")
                return
            
            # Get votes from OLIS
            votes_data = await self.client.get_all_committee_votes(session_key)
            logger.info(f"Found {len(votes_data)} committee votes for session {session_key}")
            
            if not votes_data:
                logger.info(f"No committee votes found for session {session_key}")
                return
            
            # Get existing votes for this session
            existing_stmt = select(CommitteeVote).where(CommitteeVote.session_id == session.id)
            existing_result = await db_session.execute(existing_stmt)
            existing_votes = {
                v.committee_vote_id: v for v in existing_result.scalars().all()
            }
            
            # Get measures, committees, and legislators for foreign key lookups
            measures_stmt = select(Measure).where(Measure.session_id == session.id)
            measures_result = await db_session.execute(measures_stmt)
            measures_map = {
                (m.measure_prefix, m.measure_number): m 
                for m in measures_result.scalars().all()
            }
            
            committees_stmt = select(Committee).where(Committee.session_id == session.id)
            committees_result = await db_session.execute(committees_stmt)
            committees_map = {c.committee_code: c for c in committees_result.scalars().all()}
            
            legislators_stmt = select(Legislator).where(Legislator.session_id == session.id)
            legislators_result = await db_session.execute(legislators_stmt)
            legislators_map = {l.legislator_code: l for l in legislators_result.scalars().all()}
            
            new_votes = []
            batch_size = 500
            
            for i, vote_data in enumerate(votes_data):
                try:
                    vote_id = vote_data.get('CommitteeVoteId')
                    committee_code = vote_data.get('CommitteeCode', '')
                    measure_prefix = vote_data.get('MeasurePrefix', '')
                    measure_number = self._safe_int(vote_data.get('MeasureNumber')) or 0
                    vote_name = vote_data.get('VoteName', '')
                    measure_key = (measure_prefix, measure_number)
                    
                    if vote_id in existing_votes:
                        # Update existing vote
                        vote = existing_votes[vote_id]
                        vote.meaning = vote_data.get('Meaning', '')
                        vote.olis_modified_date = self._parse_date(vote_data.get('ModifiedDate')) or datetime.now()
                        vote.last_synced_at = datetime.now()
                    else:
                        # Create new vote if all entities exist
                        measure = measures_map.get(measure_key)
                        committee = committees_map.get(committee_code)
                        legislator = legislators_map.get(vote_name)
                        
                        if measure and committee and legislator:
                            new_vote = CommitteeVote(
                                session_id=session.id,
                                committee_id=committee.id,
                                measure_id=measure.id,
                                legislator_id=legislator.id,
                                committee_vote_id=vote_id,
                                committee_report_id=vote_data.get('CommitteeReportId'),
                                committee_agenda_item_id=vote_data.get('CommitteeAgendaItemId'),
                                session_key=session_key,
                                committee_code=committee_code,
                                measure_prefix=measure_prefix,
                                measure_number=measure_number,
                                vote_name=vote_name,
                                meaning=vote_data.get('Meaning', ''),
                                meeting_date=self._parse_date(vote_data.get('MeetingDate')) or datetime.now(),
                                olis_created_date=self._parse_date(vote_data.get('CreatedDate')) or datetime.now(),
                                olis_modified_date=self._parse_date(vote_data.get('ModifiedDate')) or datetime.now()
                            )
                            new_votes.append(new_vote)
                    
                    self.sync_stats['committee_votes_processed'] += 1
                    
                    # Batch processing
                    if (i + 1) % batch_size == 0 or i == len(votes_data) - 1:
                        if new_votes:
                            db_session.add_all(new_votes)
                            logger.info(f"Added {len(new_votes)} new committee votes to batch")
                            new_votes = []
                        
                        await db_session.flush()
                        logger.info(f"Processed {i + 1}/{len(votes_data)} committee votes")
                    
                except Exception as e:
                    logger.error(f"Failed to process committee vote {vote_id}: {str(e)}")
                    self.sync_stats['errors'].append(f"Committee vote {vote_id}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to sync committee votes: {str(e)}")
            self.sync_stats['errors'].append(f"Committee votes sync error: {str(e)}")
    
    async def sync_committee_meetings(self, db_session, session: LegislativeSession, batch_size: int = 1000):
        """Sync committee meetings for a session"""
        try:
            logger.info(f"Syncing committee meetings for session {session.session_key}")
            
            meetings_data = await self.olis_client.get_all_committee_meetings(session.session_key)
            logger.info(f"Retrieved {len(meetings_data)} committee meetings from OLIS")
            
            new_meetings = []
            
            for i, meeting_data in enumerate(meetings_data):
                try:
                    committee_meeting_id = self._safe_int(meeting_data.get('CommitteeMeetingId'))
                    if not committee_meeting_id:
                        continue
                    
                    # Check if meeting exists
                    existing_meeting = await db_session.execute(
                        select(CommitteeMeeting).where(CommitteeMeeting.committee_meeting_id == committee_meeting_id)
                    )
                    existing_meeting = existing_meeting.scalar_one_or_none()
                    
                    if not existing_meeting:
                        # Find committee by code
                        committee_code = meeting_data.get('CommitteeCode', '')
                        committee_result = await db_session.execute(
                            select(Committee).where(
                                Committee.session_id == session.id,
                                Committee.committee_code == committee_code
                            )
                        )
                        committee = committee_result.scalar_one_or_none()
                        
                        if committee:
                            new_meeting = CommitteeMeeting(
                                session_id=session.id,
                                committee_id=committee.id,
                                committee_meeting_id=committee_meeting_id,
                                session_key=session.session_key,
                                committee_code=committee_code,
                                meeting_date=self._safe_datetime(meeting_data.get('MeetingDate')),
                                start_time=meeting_data.get('StartTime'),
                                end_time=meeting_data.get('EndTime'),
                                location=meeting_data.get('Location'),
                                notes=meeting_data.get('Notes'),
                                is_cancelled=self._safe_bool(meeting_data.get('IsCancelled')),
                                olis_created_date=self._safe_datetime(meeting_data.get('CreatedDate')),
                                olis_modified_date=self._safe_datetime(meeting_data.get('ModifiedDate'))
                            )
                            new_meetings.append(new_meeting)
                    
                    self.sync_stats['committee_meetings_processed'] += 1
                    
                    # Batch processing
                    if (i + 1) % batch_size == 0 or i == len(meetings_data) - 1:
                        if new_meetings:
                            db_session.add_all(new_meetings)
                            logger.info(f"Added {len(new_meetings)} new committee meetings to batch")
                            new_meetings = []
                        
                        await db_session.flush()
                        logger.info(f"Processed {i + 1}/{len(meetings_data)} committee meetings")
                    
                except Exception as e:
                    logger.error(f"Failed to process committee meeting {meeting_data.get('CommitteeMeetingId', 'Unknown')}: {str(e)}")
                    self.sync_stats['errors'].append(f"Committee meeting {meeting_data.get('CommitteeMeetingId', 'Unknown')}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to sync committee meetings: {str(e)}")
            self.sync_stats['errors'].append(f"Committee meetings sync error: {str(e)}")
    
    async def sync_agenda_items(self, db_session, session: LegislativeSession, batch_size: int = 1000):
        """Sync committee agenda items for a session"""
        try:
            logger.info(f"Syncing agenda items for session {session.session_key}")
            
            agenda_data = await self.olis_client.get_all_committee_agenda_items(session.session_key)
            logger.info(f"Retrieved {len(agenda_data)} agenda items from OLIS")
            
            new_items = []
            
            for i, item_data in enumerate(agenda_data):
                try:
                    agenda_item_id = self._safe_int(item_data.get('CommitteeAgendaItemId'))
                    if not agenda_item_id:
                        continue
                    
                    # Check if agenda item exists
                    existing_item = await db_session.execute(
                        select(CommitteeAgendaItem).where(CommitteeAgendaItem.committee_agenda_item_id == agenda_item_id)
                    )
                    existing_item = existing_item.scalar_one_or_none()
                    
                    if not existing_item:
                        # Find committee and measure by codes
                        committee_code = item_data.get('CommitteeCode', '')
                        measure_prefix = item_data.get('MeasurePrefix', '')
                        measure_number = self._safe_int(item_data.get('MeasureNumber'))
                        committee_meeting_id = self._safe_int(item_data.get('CommitteeMeetingId'))
                        
                        # Get committee
                        committee_result = await db_session.execute(
                            select(Committee).where(
                                Committee.session_id == session.id,
                                Committee.committee_code == committee_code
                            )
                        )
                        committee = committee_result.scalar_one_or_none()
                        
                        # Get measure if specified
                        measure = None
                        if measure_prefix and measure_number:
                            measure_result = await db_session.execute(
                                select(Measure).where(
                                    Measure.session_id == session.id,
                                    Measure.measure_prefix == measure_prefix,
                                    Measure.measure_number == measure_number
                                )
                            )
                            measure = measure_result.scalar_one_or_none()
                        
                        # Get committee meeting if specified
                        meeting = None
                        if committee_meeting_id:
                            meeting_result = await db_session.execute(
                                select(CommitteeMeeting).where(CommitteeMeeting.committee_meeting_id == committee_meeting_id)
                            )
                            meeting = meeting_result.scalar_one_or_none()
                        
                        if committee:
                            new_item = CommitteeAgendaItem(
                                session_id=session.id,
                                committee_id=committee.id,
                                measure_id=measure.id if measure else None,
                                committee_meeting_id=meeting.id if meeting else None,
                                committee_agenda_item_id=agenda_item_id,
                                olis_committee_meeting_id=committee_meeting_id,
                                session_key=session.session_key,
                                committee_code=committee_code,
                                measure_prefix=measure_prefix or None,
                                measure_number=measure_number,
                                item_number=self._safe_int(item_data.get('ItemNumber')),
                                agenda_item_type=item_data.get('AgendaItemType'),
                                action_taken=item_data.get('ActionTaken'),
                                notes=item_data.get('Notes'),
                                olis_created_date=self._safe_datetime(item_data.get('CreatedDate')),
                                olis_modified_date=self._safe_datetime(item_data.get('ModifiedDate'))
                            )
                            new_items.append(new_item)
                    
                    self.sync_stats['agenda_items_processed'] += 1
                    
                    # Batch processing
                    if (i + 1) % batch_size == 0 or i == len(agenda_data) - 1:
                        if new_items:
                            db_session.add_all(new_items)
                            logger.info(f"Added {len(new_items)} new agenda items to batch")
                            new_items = []
                        
                        await db_session.flush()
                        logger.info(f"Processed {i + 1}/{len(agenda_data)} agenda items")
                    
                except Exception as e:
                    logger.error(f"Failed to process agenda item {item_data.get('CommitteeAgendaItemId', 'Unknown')}: {str(e)}")
                    self.sync_stats['errors'].append(f"Agenda item {item_data.get('CommitteeAgendaItemId', 'Unknown')}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to sync agenda items: {str(e)}")
            self.sync_stats['errors'].append(f"Agenda items sync error: {str(e)}")
    
    async def sync_measure_documents(self, db_session, session: LegislativeSession, batch_size: int = 1000):
        """Sync measure documents for a session"""
        try:
            logger.info(f"Syncing measure documents for session {session.session_key}")
            
            documents_data = await self.olis_client.get_all_measure_documents(session.session_key)
            logger.info(f"Retrieved {len(documents_data)} measure documents from OLIS")
            
            new_documents = []
            
            for i, doc_data in enumerate(documents_data):
                try:
                    document_id = self._safe_int(doc_data.get('DocumentId'))
                    if not document_id:
                        continue
                    
                    # Check if document exists
                    existing_doc = await db_session.execute(
                        select(MeasureDocument).where(MeasureDocument.document_id == document_id)
                    )
                    existing_doc = existing_doc.scalar_one_or_none()
                    
                    if not existing_doc:
                        # Find measure by prefix and number
                        measure_prefix = doc_data.get('MeasurePrefix', '')
                        measure_number = self._safe_int(doc_data.get('MeasureNumber'))
                        
                        measure_result = await db_session.execute(
                            select(Measure).where(
                                Measure.session_id == session.id,
                                Measure.measure_prefix == measure_prefix,
                                Measure.measure_number == measure_number
                            )
                        )
                        measure = measure_result.scalar_one_or_none()
                        
                        if measure:
                            new_document = MeasureDocument(
                                session_id=session.id,
                                measure_id=measure.id,
                                document_id=document_id,
                                session_key=session.session_key,
                                measure_prefix=measure_prefix,
                                measure_number=measure_number,
                                document_type=doc_data.get('DocumentType'),
                                document_name=doc_data.get('DocumentName'),
                                document_description=doc_data.get('DocumentDescription'),
                                document_url=doc_data.get('DocumentUrl'),
                                file_size=self._safe_int(doc_data.get('FileSize')),
                                mime_type=doc_data.get('MimeType'),
                                is_public=self._safe_bool(doc_data.get('IsPublic')),
                                olis_created_date=self._safe_datetime(doc_data.get('CreatedDate')),
                                olis_modified_date=self._safe_datetime(doc_data.get('ModifiedDate'))
                            )
                            new_documents.append(new_document)
                    
                    self.sync_stats['measure_documents_processed'] += 1
                    
                    # Batch processing
                    if (i + 1) % batch_size == 0 or i == len(documents_data) - 1:
                        if new_documents:
                            db_session.add_all(new_documents)
                            logger.info(f"Added {len(new_documents)} new measure documents to batch")
                            new_documents = []
                        
                        await db_session.flush()
                        logger.info(f"Processed {i + 1}/{len(documents_data)} measure documents")
                    
                except Exception as e:
                    logger.error(f"Failed to process measure document {doc_data.get('DocumentId', 'Unknown')}: {str(e)}")
                    self.sync_stats['errors'].append(f"Measure document {doc_data.get('DocumentId', 'Unknown')}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to sync measure documents: {str(e)}")
            self.sync_stats['errors'].append(f"Measure documents sync error: {str(e)}")
    
    async def sync_committee_meeting_documents(self, db_session, session: LegislativeSession, batch_size: int = 1000):
        """Sync committee meeting documents for a session"""
        try:
            logger.info(f"Syncing committee meeting documents for session {session.session_key}")
            
            documents_data = await self.olis_client.get_all_committee_meeting_documents(session.session_key)
            logger.info(f"Retrieved {len(documents_data)} committee meeting documents from OLIS")
            
            new_documents = []
            
            for i, doc_data in enumerate(documents_data):
                try:
                    document_id = self._safe_int(doc_data.get('DocumentId'))
                    if not document_id:
                        continue
                    
                    # Check if document exists
                    existing_doc = await db_session.execute(
                        select(CommitteeMeetingDocument).where(CommitteeMeetingDocument.document_id == document_id)
                    )
                    existing_doc = existing_doc.scalar_one_or_none()
                    
                    if not existing_doc:
                        # Find committee and meeting
                        committee_code = doc_data.get('CommitteeCode', '')
                        committee_meeting_id = self._safe_int(doc_data.get('CommitteeMeetingId'))
                        
                        # Get committee
                        committee_result = await db_session.execute(
                            select(Committee).where(
                                Committee.session_id == session.id,
                                Committee.committee_code == committee_code
                            )
                        )
                        committee = committee_result.scalar_one_or_none()
                        
                        # Get committee meeting if specified
                        meeting = None
                        if committee_meeting_id:
                            meeting_result = await db_session.execute(
                                select(CommitteeMeeting).where(CommitteeMeeting.committee_meeting_id == committee_meeting_id)
                            )
                            meeting = meeting_result.scalar_one_or_none()
                        
                        if committee:
                            new_document = CommitteeMeetingDocument(
                                session_id=session.id,
                                committee_id=committee.id,
                                committee_meeting_id=meeting.id if meeting else None,
                                document_id=document_id,
                                olis_committee_meeting_id=committee_meeting_id,
                                session_key=session.session_key,
                                committee_code=committee_code,
                                document_type=doc_data.get('DocumentType'),
                                document_name=doc_data.get('DocumentName'),
                                document_description=doc_data.get('DocumentDescription'),
                                document_url=doc_data.get('DocumentUrl'),
                                file_size=self._safe_int(doc_data.get('FileSize')),
                                mime_type=doc_data.get('MimeType'),
                                is_public=self._safe_bool(doc_data.get('IsPublic')),
                                meeting_date=self._safe_datetime(doc_data.get('MeetingDate')),
                                olis_created_date=self._safe_datetime(doc_data.get('CreatedDate')),
                                olis_modified_date=self._safe_datetime(doc_data.get('ModifiedDate'))
                            )
                            new_documents.append(new_document)
                    
                    self.sync_stats['committee_meeting_documents_processed'] += 1
                    
                    # Batch processing
                    if (i + 1) % batch_size == 0 or i == len(documents_data) - 1:
                        if new_documents:
                            db_session.add_all(new_documents)
                            logger.info(f"Added {len(new_documents)} new committee meeting documents to batch")
                            new_documents = []
                        
                        await db_session.flush()
                        logger.info(f"Processed {i + 1}/{len(documents_data)} committee meeting documents")
                    
                except Exception as e:
                    logger.error(f"Failed to process committee meeting document {doc_data.get('DocumentId', 'Unknown')}: {str(e)}")
                    self.sync_stats['errors'].append(f"Committee meeting document {doc_data.get('DocumentId', 'Unknown')}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to sync committee meeting documents: {str(e)}")
            self.sync_stats['errors'].append(f"Committee meeting documents sync error: {str(e)}")
    
    async def sync_measure_sponsors(self, db_session: AsyncSession, session: LegislativeSession):
        """Sync measure sponsors for a session"""
        logger.info(f"Syncing measure sponsors for session: {session.session_key}")
        
        try:
            # Get sponsors from OLIS
            sponsors_data = await self.client.get_all_measure_sponsors(session.session_key)
            logger.info(f"Found {len(sponsors_data)} measure sponsors for session {session.session_key}")
            
            # Get existing sponsors for this session
            existing_stmt = select(MeasureSponsor).where(MeasureSponsor.session_id == session.id)
            existing_result = await db_session.execute(existing_stmt)
            existing_sponsors = {s.measure_sponsor_id: s for s in existing_result.scalars().all()}
            
            # Get measures and legislators for foreign key lookups
            measures_stmt = select(Measure).where(Measure.session_id == session.id)
            measures_result = await db_session.execute(measures_stmt)
            measures_map = {f"{m.measure_prefix}_{m.measure_number}": m for m in measures_result.scalars().all()}
            
            legislators_stmt = select(Legislator).where(Legislator.session_id == session.id)
            legislators_result = await db_session.execute(legislators_stmt)
            legislators_map = {l.legislator_code: l for l in legislators_result.scalars().all()}
            
            new_sponsors = []
            batch_size = 500
            
            for i, sponsor_data in enumerate(sponsors_data):
                try:
                    sponsor_id = self._safe_int(sponsor_data.get('MeasureSponsorId'))
                    if not sponsor_id:
                        continue
                    
                    if sponsor_id in existing_sponsors:
                        # Update existing sponsor
                        sponsor = existing_sponsors[sponsor_id]
                        sponsor.sponsor_name = sponsor_data.get('SponsorName', '')
                        sponsor.sponsor_type = sponsor_data.get('SponsorType', '')
                        sponsor.legislator_code = sponsor_data.get('LegislatorCode')
                        sponsor.olis_modified_date = self._parse_date(sponsor_data.get('ModifiedDate'))
                        sponsor.last_synced_at = datetime.now()
                    else:
                        # Create new sponsor
                        measure_prefix = sponsor_data.get('MeasurePrefix', '')
                        measure_number = self._safe_int(sponsor_data.get('MeasureNumber'))
                        measure_key = f"{measure_prefix}_{measure_number}"
                        
                        measure = measures_map.get(measure_key)
                        if not measure:
                            logger.warning(f"Measure {measure_prefix} {measure_number} not found for sponsor {sponsor_id}")
                            continue
                        
                        # Try to link to legislator
                        legislator_code = sponsor_data.get('LegislatorCode')
                        legislator = legislators_map.get(legislator_code) if legislator_code else None
                        
                        new_sponsor = MeasureSponsor(
                            session_id=session.id,
                            measure_id=measure.id,
                            legislator_id=legislator.id if legislator else None,
                            measure_sponsor_id=sponsor_id,
                            session_key=session.session_key,
                            measure_prefix=measure_prefix,
                            measure_number=measure_number,
                            sponsor_name=sponsor_data.get('SponsorName', ''),
                            sponsor_type=sponsor_data.get('SponsorType', ''),
                            legislator_code=legislator_code,
                            sponsor_order=self._safe_int(sponsor_data.get('SponsorOrder', 0)),
                            olis_created_date=self._parse_date(sponsor_data.get('CreatedDate')),
                            olis_modified_date=self._parse_date(sponsor_data.get('ModifiedDate'))
                        )
                        new_sponsors.append(new_sponsor)
                    
                    self.sync_stats['measure_sponsors_processed'] += 1
                    
                    # Batch processing
                    if (i + 1) % batch_size == 0 or i == len(sponsors_data) - 1:
                        if new_sponsors:
                            db_session.add_all(new_sponsors)
                            logger.info(f"Added {len(new_sponsors)} new measure sponsors to batch")
                            new_sponsors = []
                        
                        await db_session.flush()
                        logger.info(f"Processed {i + 1}/{len(sponsors_data)} measure sponsors")
                    
                except Exception as e:
                    logger.error(f"Failed to process measure sponsor {sponsor_data.get('MeasureSponsorId', 'Unknown')}: {str(e)}")
                    self.sync_stats['errors'].append(f"Measure sponsor {sponsor_data.get('MeasureSponsorId', 'Unknown')}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to sync measure sponsors: {str(e)}")
            self.sync_stats['errors'].append(f"Measure sponsors sync error: {str(e)}")
    
    async def sync_committee_proposed_amendments(self, db_session: AsyncSession, session: LegislativeSession):
        """Sync committee proposed amendments for a session"""
        logger.info(f"Syncing committee proposed amendments for session: {session.session_key}")
        
        try:
            # Get amendments from OLIS
            amendments_data = await self.client.get_all_committee_proposed_amendments(session.session_key)
            logger.info(f"Found {len(amendments_data)} committee proposed amendments for session {session.session_key}")
            
            # Get existing amendments for this session
            existing_stmt = select(CommitteeProposedAmendment).where(CommitteeProposedAmendment.session_id == session.id)
            existing_result = await db_session.execute(existing_stmt)
            existing_amendments = {a.proposed_amendment_id: a for a in existing_result.scalars().all()}
            
            # Get lookups for foreign keys
            measures_stmt = select(Measure).where(Measure.session_id == session.id)
            measures_result = await db_session.execute(measures_stmt)
            measures_map = {f"{m.measure_prefix}_{m.measure_number}": m for m in measures_result.scalars().all()}
            
            committees_stmt = select(Committee).where(Committee.session_id == session.id)
            committees_result = await db_session.execute(committees_stmt)
            committees_map = {c.committee_code: c for c in committees_result.scalars().all()}
            
            agenda_items_stmt = select(CommitteeAgendaItem).where(CommitteeAgendaItem.session_id == session.id)
            agenda_items_result = await db_session.execute(agenda_items_stmt)
            agenda_items_map = {a.committee_agenda_item_id: a for a in agenda_items_result.scalars().all()}
            
            new_amendments = []
            batch_size = 500
            
            for i, amendment_data in enumerate(amendments_data):
                try:
                    amendment_id = self._safe_int(amendment_data.get('ProposedAmendmentId'))
                    if not amendment_id:
                        continue
                    
                    if amendment_id in existing_amendments:
                        # Update existing amendment
                        amendment = existing_amendments[amendment_id]
                        amendment.meaning = amendment_data.get('Meaning', '')
                        amendment.proposed_amendment_url = amendment_data.get('ProposedAmendmentUrl', '')
                        amendment.olis_modified_date = self._parse_date(amendment_data.get('ModifiedDate'))
                        amendment.last_synced_at = datetime.now()
                    else:
                        # Create new amendment
                        measure_prefix = amendment_data.get('MeasurePrefix', '')
                        measure_number = self._safe_int(amendment_data.get('MeasureNumber'))
                        measure_key = f"{measure_prefix}_{measure_number}"
                        committee_code = amendment_data.get('CommitteeCode', '')
                        
                        # Get required relationships
                        measure = measures_map.get(measure_key)
                        committee = committees_map.get(committee_code)
                        
                        if not committee:
                            logger.warning(f"Committee {committee_code} not found for amendment {amendment_id}")
                            continue
                        
                        # Optional agenda item relationship
                        agenda_item_id = self._safe_int(amendment_data.get('CommitteeAgendaItemId'))
                        agenda_item = agenda_items_map.get(agenda_item_id) if agenda_item_id else None
                        
                        new_amendment = CommitteeProposedAmendment(
                            session_id=session.id,
                            committee_id=committee.id,
                            measure_id=measure.id if measure else None,
                            agenda_item_id=agenda_item.id if agenda_item else None,
                            proposed_amendment_id=amendment_id,
                            committee_agenda_item_id=agenda_item_id,
                            session_key=session.session_key,
                            committee_code=committee_code,
                            meeting_date=self._parse_date(amendment_data.get('MeetingDate')),
                            measure_prefix=measure_prefix,
                            measure_number=measure_number or 0,
                            amendment_number=amendment_data.get('AmendmentNumber', ''),
                            meaning=amendment_data.get('Meaning', ''),
                            proposed_amendment_url=amendment_data.get('ProposedAmendmentUrl', ''),
                            olis_created_date=self._parse_date(amendment_data.get('CreatedDate')),
                            olis_modified_date=self._parse_date(amendment_data.get('ModifiedDate'))
                        )
                        new_amendments.append(new_amendment)
                    
                    self.sync_stats['committee_proposed_amendments_processed'] += 1
                    
                    # Batch processing
                    if (i + 1) % batch_size == 0 or i == len(amendments_data) - 1:
                        if new_amendments:
                            db_session.add_all(new_amendments)
                            logger.info(f"Added {len(new_amendments)} new committee proposed amendments to batch")
                            new_amendments = []
                        
                        await db_session.flush()
                        logger.info(f"Processed {i + 1}/{len(amendments_data)} committee proposed amendments")
                    
                except Exception as e:
                    logger.error(f"Failed to process committee proposed amendment {amendment_data.get('ProposedAmendmentId', 'Unknown')}: {str(e)}")
                    self.sync_stats['errors'].append(f"Committee proposed amendment {amendment_data.get('ProposedAmendmentId', 'Unknown')}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to sync committee proposed amendments: {str(e)}")
            self.sync_stats['errors'].append(f"Committee proposed amendments sync error: {str(e)}")
    
    async def sync_floor_session_agenda_items(self, db_session: AsyncSession, session: LegislativeSession):
        """Sync floor session agenda items for a session"""
        logger.info(f"Syncing floor session agenda items for session: {session.session_key}")
        
        try:
            # Get agenda items from OLIS
            items_data = await self.client.get_all_floor_session_agenda_items(session.session_key)
            logger.info(f"Found {len(items_data)} floor session agenda items for session {session.session_key}")
            
            # Get existing items for this session
            existing_stmt = select(FloorSessionAgendaItem).where(FloorSessionAgendaItem.session_id == session.id)
            existing_result = await db_session.execute(existing_stmt)
            existing_items = {i.agenda_id: i for i in existing_result.scalars().all()}
            
            # Get measures for foreign key lookup
            measures_stmt = select(Measure).where(Measure.session_id == session.id)
            measures_result = await db_session.execute(measures_stmt)
            measures_map = {f"{m.measure_prefix}_{m.measure_number}": m for m in measures_result.scalars().all()}
            
            new_items = []
            batch_size = 500
            
            for i, item_data in enumerate(items_data):
                try:
                    agenda_id = self._safe_int(item_data.get('AgendaId'))
                    if not agenda_id:
                        continue
                    
                    if agenda_id in existing_items:
                        # Update existing item
                        item = existing_items[agenda_id]
                        item.schedule_date = self._parse_date(item_data.get('ScheduleDate'))
                        item.version = item_data.get('Version')
                        item.completed = self._safe_bool(item_data.get('Completed'))
                        item.order_of_business = item_data.get('OrderOfBusiness', '')
                        item.carrier_code = item_data.get('CarrierCode')
                        item.olis_modified_date = self._parse_date(item_data.get('ModifiedDate'))
                        item.last_synced_at = datetime.now()
                    else:
                        # Create new item
                        measure_prefix = item_data.get('MeasurePrefix', '')
                        measure_number = self._safe_int(item_data.get('MeasureNumber'))
                        measure_key = f"{measure_prefix}_{measure_number}"
                        
                        # Optional measure relationship
                        measure = measures_map.get(measure_key)
                        
                        new_item = FloorSessionAgendaItem(
                            session_id=session.id,
                            measure_id=measure.id if measure else None,
                            agenda_id=agenda_id,
                            session_key=session.session_key,
                            measure_prefix=measure_prefix,
                            measure_number=measure_number or 0,
                            schedule_date=self._parse_date(item_data.get('ScheduleDate')),
                            version=item_data.get('Version'),
                            chamber=item_data.get('Chamber', ''),
                            completed=self._safe_bool(item_data.get('Completed')),
                            order_of_business=item_data.get('OrderOfBusiness', ''),
                            carrier_code=item_data.get('CarrierCode'),
                            olis_created_date=self._parse_date(item_data.get('CreatedDate')),
                            olis_modified_date=self._parse_date(item_data.get('ModifiedDate'))
                        )
                        new_items.append(new_item)
                    
                    self.sync_stats['floor_session_agenda_items_processed'] += 1
                    
                    # Batch processing
                    if (i + 1) % batch_size == 0 or i == len(items_data) - 1:
                        if new_items:
                            db_session.add_all(new_items)
                            logger.info(f"Added {len(new_items)} new floor session agenda items to batch")
                            new_items = []
                        
                        await db_session.flush()
                        logger.info(f"Processed {i + 1}/{len(items_data)} floor session agenda items")
                    
                except Exception as e:
                    logger.error(f"Failed to process floor session agenda item {item_data.get('AgendaId', 'Unknown')}: {str(e)}")
                    self.sync_stats['errors'].append(f"Floor session agenda item {item_data.get('AgendaId', 'Unknown')}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to sync floor session agenda items: {str(e)}")
            self.sync_stats['errors'].append(f"Floor session agenda items sync error: {str(e)}")

    async def sync_floor_letters(self, db_session: AsyncSession, session: LegislativeSession):
        """Sync floor letters for a session"""
        logger.info(f"Syncing floor letters for session: {session.session_key}")
        
        try:
            # Get floor letters from OLIS
            letters_data = await self.olis_client.get_all_floor_letters(session.session_key)
            
            if not letters_data:
                logger.info(f"No floor letters found for session {session.session_key}")
                return
            
            logger.info(f"Processing {len(letters_data)} floor letters for session {session.session_key}")
            
            batch_size = 500
            new_items = []
            
            for i, letter_data in enumerate(letters_data):
                try:
                    floor_letter_id = letter_data.get('FloorLetterId')
                    if not floor_letter_id:
                        logger.warning(f"Missing FloorLetterId in floor letter data: {letter_data}")
                        continue
                    
                    # Check if floor letter already exists
                    existing_query = select(FloorLetter).where(FloorLetter.floor_letter_id == floor_letter_id)
                    result = await db_session.execute(existing_query)
                    existing_letter = result.scalar_one_or_none()
                    
                    if existing_letter:
                        # Update existing record
                        existing_letter.letter_date = self._parse_date(letter_data.get('LetterDate'))
                        existing_letter.chamber = letter_data.get('Chamber', '')
                        existing_letter.letter_description = letter_data.get('LetterDescription', '')
                        existing_letter.letter_title = letter_data.get('LetterTitle', '')
                        existing_letter.floor_letter_url = letter_data.get('FloorLetterUrl', '')
                        existing_letter.measure_prefix = letter_data.get('MeasurePrefix')
                        existing_letter.measure_number = letter_data.get('MeasureNumber')
                        existing_letter.last_synced_at = datetime.now(timezone.utc)
                        
                        # Update measure relationship if available
                        if letter_data.get('MeasurePrefix') and letter_data.get('MeasureNumber'):
                            measure_query = select(Measure).where(
                                Measure.session_id == session.id,
                                Measure.measure_prefix == letter_data.get('MeasurePrefix'),
                                Measure.measure_number == letter_data.get('MeasureNumber')
                            )
                            measure_result = await db_session.execute(measure_query)
                            measure = measure_result.scalar_one_or_none()
                            if measure:
                                existing_letter.measure_id = measure.id
                    else:
                        # Find associated measure if any
                        measure = None
                        if letter_data.get('MeasurePrefix') and letter_data.get('MeasureNumber'):
                            measure_query = select(Measure).where(
                                Measure.session_id == session.id,
                                Measure.measure_prefix == letter_data.get('MeasurePrefix'),
                                Measure.measure_number == letter_data.get('MeasureNumber')
                            )
                            measure_result = await db_session.execute(measure_query)
                            measure = measure_result.scalar_one_or_none()
                        
                        # Create new floor letter
                        new_letter = FloorLetter(
                            session_id=session.id,
                            measure_id=measure.id if measure else None,
                            floor_letter_id=floor_letter_id,
                            session_key=session.session_key,
                            measure_prefix=letter_data.get('MeasurePrefix'),
                            measure_number=letter_data.get('MeasureNumber'),
                            letter_date=self._parse_date(letter_data.get('LetterDate')),
                            chamber=letter_data.get('Chamber', ''),
                            letter_description=letter_data.get('LetterDescription', ''),
                            letter_title=letter_data.get('LetterTitle', ''),
                            floor_letter_url=letter_data.get('FloorLetterUrl', '')
                        )
                        new_items.append(new_letter)
                    
                    self.sync_stats['floor_letters_processed'] += 1
                    
                    # Batch processing
                    if (i + 1) % batch_size == 0 or i == len(letters_data) - 1:
                        if new_items:
                            db_session.add_all(new_items)
                            logger.info(f"Added {len(new_items)} new floor letters to batch")
                            new_items = []
                        
                        await db_session.flush()
                        logger.info(f"Processed {i + 1}/{len(letters_data)} floor letters")
                    
                except Exception as e:
                    logger.error(f"Failed to process floor letter {letter_data.get('FloorLetterId', 'Unknown')}: {str(e)}")
                    self.sync_stats['errors'].append(f"Floor letter {letter_data.get('FloorLetterId', 'Unknown')}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to sync floor letters: {str(e)}")
            self.sync_stats['errors'].append(f"Floor letters sync error: {str(e)}")

# Global instance
sync_service = OLISSyncService()

# Async function for API endpoint usage
async def run_olis_sync(session_key: str = None) -> Dict[str, Any]:
    """
    Run OLIS synchronization
    
    Args:
        session_key: Optional session key to sync specific session
        
    Returns:
        Sync results and statistics
    """
    try:
        results = await sync_service.sync_session_data(session_key)
        return {
            'status': 'success',
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"OLIS sync failed: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }