"""
Enhanced Bill Status Classification
Provides better categorization of Oregon legislative bills based on OLIS data
"""

from typing import Dict, Any, List
from datetime import datetime
import re
from committee_mapping import get_committee_info, get_committees_by_chamber, get_committee_display_name

def classify_bill_status(measure: Dict[str, Any]) -> str:
    """
    Classify a bill's status based on available OLIS data fields
    
    Args:
        measure: Bill data from OLIS API
        
    Returns:
        Status category string
    """
    current_location = (measure.get('CurrentLocation', '') or '').strip()
    vetoed = measure.get('Vetoed', False)
    chapter_number = measure.get('ChapterNumber')
    measure_prefix = measure.get('MeasurePrefix', '')
    effective_date = measure.get('EffectiveDate')
    
    # Handle vetoed bills first
    if vetoed:
        return 'vetoed'
    
    # Handle enacted bills (have chapter numbers)
    if chapter_number:
        return 'signed_enacted'
    
    # Handle filed/completed items (mostly resolutions)
    if 'filed with secretary of state' in current_location.lower():
        # For resolutions, this often means completed/passed
        if measure_prefix in ['HCR', 'SCR', 'HR', 'SR', 'HJR', 'SJR', 'HJM', 'SJM']:
            return 'filed_completed'
        else:
            return 'filed_completed'
    
    # Handle committee status
    if 'in senate committee' in current_location.lower():
        return 'in_senate_committee'
    
    if 'in house committee' in current_location.lower():
        return 'in_house_committee'
    
    # Handle floor activity
    if any(term in current_location.lower() for term in ['floor', 'third reading', 'second reading']):
        if 'senate' in current_location.lower():
            return 'senate_floor'
        elif 'house' in current_location.lower():
            return 'house_floor'
        else:
            return 'floor_action'
    
    # Handle passed chambers
    if 'passed senate' in current_location.lower():
        return 'passed_senate'
    
    if 'passed house' in current_location.lower():
        return 'passed_house'
    
    # Handle governor/executive actions
    if any(term in current_location.lower() for term in ['governor', 'executive']):
        return 'with_governor'
    
    # Handle failed/dead bills
    if any(term in current_location.lower() for term in ['dead', 'failed', 'withdrawn', 'indefinitely postponed']):
        return 'failed'
    
    # Handle bills that have been introduced but not yet assigned
    if 'introduced' in current_location.lower():
        return 'introduced'
    
    # Default fallback based on patterns
    if current_location:
        return 'in_process'
    else:
        return 'unknown'

def get_status_display_info(status: str) -> Dict[str, str]:
    """
    Get display information for a status category
    
    Returns:
        Dictionary with display_name, color, and description
    """
    status_info = {
        'introduced': {
            'display_name': 'Introduced',
            'color': 'info',
            'description': 'Bill has been introduced and assigned a number'
        },
        'in_house_committee': {
            'display_name': 'House Committee',
            'color': 'primary',
            'description': 'Being reviewed by a House committee'
        },
        'in_senate_committee': {
            'display_name': 'Senate Committee',
            'color': 'primary',
            'description': 'Being reviewed by a Senate committee'
        },
        'house_floor': {
            'display_name': 'House Floor',
            'color': 'warning',
            'description': 'On House floor for voting'
        },
        'senate_floor': {
            'display_name': 'Senate Floor',
            'color': 'warning',
            'description': 'On Senate floor for voting'
        },
        'floor_action': {
            'display_name': 'Floor Action',
            'color': 'warning',
            'description': 'On floor for voting'
        },
        'passed_house': {
            'display_name': 'Passed House',
            'color': 'success',
            'description': 'Passed the House, moving to Senate'
        },
        'passed_senate': {
            'display_name': 'Passed Senate',
            'color': 'success',
            'description': 'Passed the Senate, moving to House'
        },
        'with_governor': {
            'display_name': 'With Governor',
            'color': 'warning',
            'description': 'Sent to Governor for signature'
        },
        'signed_enacted': {
            'display_name': 'Signed/Enacted',
            'color': 'success',
            'description': 'Signed by Governor and became law'
        },
        'filed_completed': {
            'display_name': 'Filed/Completed',
            'color': 'success',
            'description': 'Filed with Secretary of State (resolutions/memorials)'
        },
        'vetoed': {
            'display_name': 'Vetoed',
            'color': 'danger',
            'description': 'Vetoed by Governor'
        },
        'failed': {
            'display_name': 'Failed',
            'color': 'danger',
            'description': 'Failed to pass or was withdrawn'
        },
        'in_process': {
            'display_name': 'In Process',
            'color': 'secondary',
            'description': 'Moving through the legislative process'
        },
        'unknown': {
            'display_name': 'Unknown Status',
            'color': 'secondary',
            'description': 'Status could not be determined'
        }
    }
    
    return status_info.get(status, status_info['unknown'])

def categorize_bills_by_status(measures: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Categorize a list of bills by their status and bill type
    
    Args:
        measures: List of bill data from OLIS API
        
    Returns:
        Dictionary with status counts, bill type counts, and other statistics
    """
    status_counts = {}
    bill_type_counts = {}
    total_bills = len(measures)
    
    for measure in measures:
        # Get enhanced status
        status = classify_bill_status(measure)
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count bill types
        bill_type = measure.get('MeasurePrefix', 'Unknown')
        bill_type_counts[bill_type] = bill_type_counts.get(bill_type, 0) + 1
    
    # Get display info for all statuses
    status_display = {}
    for status, count in status_counts.items():
        display_info = get_status_display_info(status)
        status_display[status] = {
            'count': count,
            'percentage': round((count / total_bills) * 100, 1) if total_bills > 0 else 0,
            **display_info
        }
    
    return {
        'total_bills': total_bills,
        'status_counts': status_counts,
        'status_display': status_display,
        'bill_type_counts': bill_type_counts,
        'bill_types': len(bill_type_counts)
    }

def categorize_bills_by_committees(measures: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Categorize bills by the committees they are currently in
    
    Args:
        measures: List of bill data from OLIS API
        
    Returns:
        Dictionary with committee counts and display information
    """
    committee_counts = {}
    total_in_committees = 0
    
    for measure in measures:
        current_location = (measure.get('CurrentLocation', '') or '').strip().lower()
        
        if 'in house committee' in current_location:
            committee_counts['house_committees'] = committee_counts.get('house_committees', 0) + 1
            total_in_committees += 1
        elif 'in senate committee' in current_location:
            committee_counts['senate_committees'] = committee_counts.get('senate_committees', 0) + 1
            total_in_committees += 1
        elif 'joint committee' in current_location:
            committee_counts['joint_committees'] = committee_counts.get('joint_committees', 0) + 1
            total_in_committees += 1
    
    # Create display information for committees
    committee_display = {}
    for committee_type, count in committee_counts.items():
        if committee_type == 'house_committees':
            committee_display[committee_type] = {
                'count': count,
                'percentage': round((count / total_in_committees) * 100, 1) if total_in_committees > 0 else 0,
                'display_name': 'House Committees',
                'description': f'{count} bills currently in House committees',
                'chamber': 'house'
            }
        elif committee_type == 'senate_committees':
            committee_display[committee_type] = {
                'count': count,
                'percentage': round((count / total_in_committees) * 100, 1) if total_in_committees > 0 else 0,
                'display_name': 'Senate Committees',
                'description': f'{count} bills currently in Senate committees',
                'chamber': 'senate'
            }
        elif committee_type == 'joint_committees':
            committee_display[committee_type] = {
                'count': count,
                'percentage': round((count / total_in_committees) * 100, 1) if total_in_committees > 0 else 0,
                'display_name': 'Joint Committees',
                'description': f'{count} bills currently in joint committees',
                'chamber': 'joint'
            }
    
    return {
        'total_in_committees': total_in_committees,
        'committee_counts': committee_counts,
        'committee_display': committee_display
    }

def get_bill_type_info(prefix: str) -> Dict[str, str]:
    """
    Get information about a bill type prefix
    
    Args:
        prefix: Bill prefix (HB, SB, etc.)
        
    Returns:
        Dictionary with full name and description
    """
    bill_types = {
        'HB': {'name': 'House Bill', 'description': 'Legislation originating in the House'},
        'SB': {'name': 'Senate Bill', 'description': 'Legislation originating in the Senate'},
        'HCR': {'name': 'House Concurrent Resolution', 'description': 'House resolution requiring Senate agreement'},
        'SCR': {'name': 'Senate Concurrent Resolution', 'description': 'Senate resolution requiring House agreement'},
        'HR': {'name': 'House Resolution', 'description': 'House-only resolution'},
        'SR': {'name': 'Senate Resolution', 'description': 'Senate-only resolution'},
        'HJR': {'name': 'House Joint Resolution', 'description': 'Constitutional amendment from House'},
        'SJR': {'name': 'Senate Joint Resolution', 'description': 'Constitutional amendment from Senate'},
        'HJM': {'name': 'House Joint Memorial', 'description': 'House memorial to federal government'},
        'SJM': {'name': 'Senate Joint Memorial', 'description': 'Senate memorial to federal government'}
    }
    
    return bill_types.get(prefix, {'name': f'Unknown ({prefix})', 'description': 'Unknown bill type'})

def categorize_bills_by_specific_committees(measures: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Categorize bills by specific committees using OLIS committee codes
    
    Args:
        measures: List of bill data from OLIS API
        
    Returns:
        Dictionary with specific committee counts organized by chamber
    """
    house_committees = {}
    senate_committees = {}
    joint_committees = {}
    unknown_committees = {}
    total_in_committees = 0
    
    for measure in measures:
        current_location = (measure.get('CurrentLocation', '') or '').strip().lower()
        committee_code = (measure.get('CurrentCommitteeCode', '') or '').strip()
        
        # Only process bills that are currently in committees and have a committee code
        if 'committee' in current_location and committee_code:
            total_in_committees += 1
            committee_info = get_committee_info(committee_code)
            
            if committee_info:
                # Organize by chamber
                if committee_info.chamber == 'house':
                    house_committees[committee_code] = house_committees.get(committee_code, 0) + 1
                elif committee_info.chamber == 'senate':
                    senate_committees[committee_code] = senate_committees.get(committee_code, 0) + 1
                elif committee_info.chamber == 'joint':
                    joint_committees[committee_code] = joint_committees.get(committee_code, 0) + 1
            else:
                # Track unknown committee codes for debugging
                unknown_committees[committee_code] = unknown_committees.get(committee_code, 0) + 1
    
    # Create display information for each committee
    def create_committee_display(committee_dict: Dict[str, int], chamber: str) -> Dict[str, Any]:
        display_dict = {}
        for code, count in committee_dict.items():
            committee_info = get_committee_info(code)
            if committee_info:
                percentage = round((count / total_in_committees) * 100, 1) if total_in_committees > 0 else 0
                display_dict[code] = {
                    'count': count,
                    'percentage': percentage,
                    'display_name': committee_info.short_name,
                    'full_name': committee_info.full_name,
                    'description': committee_info.description,
                    'chamber': chamber,
                    'committee_code': code
                }
        # Sort by count (descending)
        return dict(sorted(display_dict.items(), key=lambda x: x[1]['count'], reverse=True))
    
    return {
        'total_in_committees': total_in_committees,
        'house_committees': {
            'count': len(house_committees),
            'bills': sum(house_committees.values()),
            'committees': create_committee_display(house_committees, 'house')
        },
        'senate_committees': {
            'count': len(senate_committees),
            'bills': sum(senate_committees.values()),
            'committees': create_committee_display(senate_committees, 'senate')
        },
        'joint_committees': {
            'count': len(joint_committees),
            'bills': sum(joint_committees.values()),
            'committees': create_committee_display(joint_committees, 'joint')
        },
        'unknown_committees': unknown_committees  # For debugging
    }