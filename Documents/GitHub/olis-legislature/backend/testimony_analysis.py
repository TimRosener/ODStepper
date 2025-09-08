"""
Hot Bills Analysis based on testimony volume and diversity
"""

from typing import Dict, Any, List
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import math
import re

def analyze_testimony_position(testimony_record: Dict) -> str:
    """
    Analyze testimony position using actual PositionOnMeasureId from OLIS data.
    Returns 'in_favor', 'against', 'neutral', or 'unknown'
    
    Based on analysis of OLIS data:
    - Most testimonies use PositionOnMeasureId values: 3981, 3982, 3983
    - These correspond to different position types but exact text mappings are not accessible via API
    """
    position_id = testimony_record.get('PositionOnMeasureId')
    
    if not position_id:
        return 'unknown'
    
    # Position ID mapping based on OLIS data patterns
    # Note: These mappings are inferred from data distribution patterns
    # The actual position text (like "Oppose", "Support", "Neutral") is not accessible via public API
    position_mapping = {
        3981: 'neutral',     # Least common - likely neutral/informational
        3982: 'in_favor',    # Most common - likely support/in favor  
        3983: 'against',     # Moderately common - likely oppose/against
    }
    
    return position_mapping.get(position_id, 'unknown')

def analyze_submitter_breakdown(testimonies: List[Dict]) -> Dict[str, Any]:
    """
    Analyze the breakdown of testimony submitters by type and characteristics
    """
    organizations = set()
    individuals = set()
    submitter_types = {
        'organizations': 0,
        'individuals': 0,
        'government': 0,
        'business': 0,
        'nonprofit': 0,
        'other': 0
    }
    
    # Government indicators
    government_keywords = ['department', 'agency', 'bureau', 'office', 'division', 'commission', 'board', 'city', 'county', 'state']
    business_keywords = ['company', 'corporation', 'llc', 'inc', 'business', 'industry', 'association', 'chamber']
    nonprofit_keywords = ['foundation', 'nonprofit', 'charity', 'organization', 'coalition', 'alliance', 'society', 'union']
    
    for testimony in testimonies:
        org = testimony.get('Organization', '').strip()
        name = f"{testimony.get('SubmitterFirstName', '')} {testimony.get('SubmitterLastName', '')}".strip()
        
        if org and org.lower() not in ['n/a', 'none', 'individual', '']:
            organizations.add(org.lower())
            submitter_types['organizations'] += 1
            
            # Categorize organization type
            org_lower = org.lower()
            if any(keyword in org_lower for keyword in government_keywords):
                submitter_types['government'] += 1
            elif any(keyword in org_lower for keyword in business_keywords):
                submitter_types['business'] += 1
            elif any(keyword in org_lower for keyword in nonprofit_keywords):
                submitter_types['nonprofit'] += 1
            else:
                submitter_types['other'] += 1
        elif name:
            individuals.add(name.lower())
            submitter_types['individuals'] += 1
    
    return {
        'unique_organizations': len(organizations),
        'unique_individuals': len(individuals),
        'submitter_types': submitter_types,
        'total_unique_submitters': len(organizations) + len(individuals)
    }

def analyze_top_submitters(testimonies: List[Dict], top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Analyze top submitters by city/location and individuals
    
    Note: The 'Organization' field in OLIS actually contains the city/location
    the submitter is from, not the organization they represent.
    
    Args:
        testimonies: List of testimony records
        top_n: Number of top submitters to return (default 10)
        
    Returns:
        List of top submitters by city/location with their counts and types
    """
    submitter_counts = Counter()
    submitter_types = {}  # Track whether each submitter is city or individual
    
    for testimony in testimonies:
        city = testimony.get('Organization', '')  # This is actually the city/location
        if city is None:
            city = ''
        else:
            city = city.strip()
            
        first_name = testimony.get('SubmitterFirstName', '') or ''
        last_name = testimony.get('SubmitterLastName', '') or ''
        name = f"{first_name} {last_name}".strip()
        
        # Determine submitter identity and type
        if city and city.lower() not in ['n/a', 'none', 'individual', '']:
            submitter_id = city
            submitter_types[submitter_id] = 'city'
        elif name:
            submitter_id = name
            submitter_types[submitter_id] = 'individual'
        else:
            continue  # Skip if no valid submitter
        
        submitter_counts[submitter_id] += 1
    
    # Get top N submitters
    top_submitters = []
    for submitter_id, count in submitter_counts.most_common(top_n):
        # Determine emoji based on type
        if submitter_types[submitter_id] == 'individual':
            emoji = '👤'
        else:
            # For cities/locations, use building/city emoji
            emoji = '🏙️'
            
        top_submitters.append({
            'name': submitter_id,
            'count': count,
            'type': submitter_types[submitter_id],
            'emoji': emoji
        })
    
    return top_submitters

def analyze_top_on_behalf_of(testimonies: List[Dict], top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Analyze top "on behalf of" organizations by counting testimonies
    
    Args:
        testimonies: List of testimony records
        top_n: Number of top organizations to return (default 10)
        
    Returns:
        List of top "on behalf of" organizations with their counts
    """
    behalf_counts = Counter()
    
    for testimony in testimonies:
        behalf_of = testimony.get('BehalfOf', '')
        
        # Handle None values
        if behalf_of is None:
            behalf_of = ''
        else:
            behalf_of = behalf_of.strip()
        
        # Skip empty or invalid entries
        if behalf_of and behalf_of.lower() not in ['n/a', 'none', '', 'individual', 'self']:
            behalf_counts[behalf_of] += 1
    
    # Get top N organizations being represented
    top_behalf_of = []
    for behalf_name, count in behalf_counts.most_common(top_n):
        top_behalf_of.append({
            'name': behalf_name,
            'count': count,
            'emoji': '🏛️'  # Using building emoji for organizations
        })
    
    return top_behalf_of

def analyze_timeline_breakdown(testimonies: List[Dict]) -> Dict[str, Any]:
    """
    Analyze testimony timeline patterns
    """
    timeline_data = {
        'recent_30_days': 0,
        'recent_90_days': 0,
        'this_year': 0,
        'older': 0,
        'date_breakdown': defaultdict(int),
        'monthly_breakdown': defaultdict(int)
    }
    
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    ninety_days_ago = now - timedelta(days=90)
    year_start = datetime(now.year, 1, 1)
    
    for testimony in testimonies:
        meeting_date_str = testimony.get('MeetingDate', '')
        if meeting_date_str:
            try:
                # Parse date (handle various formats)
                meeting_date = datetime.fromisoformat(meeting_date_str.replace('T', ' ').replace('Z', ''))
                
                # Timeline categorization
                if meeting_date >= thirty_days_ago:
                    timeline_data['recent_30_days'] += 1
                if meeting_date >= ninety_days_ago:
                    timeline_data['recent_90_days'] += 1
                if meeting_date >= year_start:
                    timeline_data['this_year'] += 1
                else:
                    timeline_data['older'] += 1
                
                # Date breakdown
                date_key = meeting_date.strftime('%Y-%m-%d')
                timeline_data['date_breakdown'][date_key] += 1
                
                # Monthly breakdown
                month_key = meeting_date.strftime('%Y-%m')
                timeline_data['monthly_breakdown'][month_key] += 1
                
            except:
                timeline_data['older'] += 1  # Assume old if we can't parse
    
    return timeline_data

async def analyze_hot_bills(client, session_key: str, limit: int = 10) -> Dict[str, Any]:
    """
    Analyze bills by testimony volume and diversity to find the hottest bills
    
    Args:
        client: OLISClient instance
        session_key: Legislative session key (e.g., "2025R1") 
        limit: Number of hot bills to return (default 10)
        
    Returns:
        Dictionary with hot bills data and analysis
    """
    try:
        # Get all testimony data for the session
        testimony_data = await client._make_request("CommitteePublicTestimonies", {
            "$filter": f"SessionKey eq '{session_key}'",
            "$orderby": "MeetingDate desc"
        })
        
        if not testimony_data:
            return {
                'hot_bills': [],
                'total_testimonies': 0,
                'bills_with_testimony': 0,
                'analysis_date': datetime.now().isoformat()
            }
        
        # Handle different response formats
        if isinstance(testimony_data, dict) and "value" in testimony_data:
            testimonies = testimony_data["value"]
        elif isinstance(testimony_data, list):
            testimonies = testimony_data
        else:
            testimonies = [testimony_data]
        
        # Group testimonies by bill
        bill_testimonies = defaultdict(list)
        
        for testimony in testimonies:
            bill_key = f"{testimony.get('MeasurePrefix', '')}{testimony.get('MeasureNumber', '')}"
            if bill_key.strip():  # Only include valid bill keys
                bill_testimonies[bill_key].append(testimony)
        
        # Calculate hotness scores for each bill
        hot_bills_data = []
        
        for bill_id, bill_testimonies_list in bill_testimonies.items():
            if not bill_testimonies_list:
                continue
                
            # Get basic bill info from first testimony
            first_testimony = bill_testimonies_list[0]
            measure_prefix = first_testimony.get('MeasurePrefix', '')
            measure_number = first_testimony.get('MeasureNumber', '')
            
            # Calculate comprehensive metrics
            total_testimonies = len(bill_testimonies_list)
            
            # Enhanced submitter analysis
            submitter_analysis = analyze_submitter_breakdown(bill_testimonies_list)
            unique_organizations = submitter_analysis['unique_organizations']
            unique_individuals = submitter_analysis['unique_individuals'] 
            total_unique_submitters = submitter_analysis['total_unique_submitters']
            submitter_types = submitter_analysis['submitter_types']
            
            # Timeline analysis
            timeline_analysis = analyze_timeline_breakdown(bill_testimonies_list)
            recent_testimonies = timeline_analysis['recent_30_days']
            
            # Top submitters analysis (by city/location)
            top_submitters = analyze_top_submitters(bill_testimonies_list, top_n=10)
            
            # Top "on behalf of" analysis
            top_behalf_of = analyze_top_on_behalf_of(bill_testimonies_list, top_n=10)
            
            # Position analysis (text-based inference)
            position_breakdown = {
                'in_favor': 0,
                'against': 0,
                'neutral': 0,
                'unknown': 0
            }
            
            for testimony in bill_testimonies_list:
                # Analyze position using actual PositionOnMeasureId from OLIS data
                position = analyze_testimony_position(testimony)
                position_breakdown[position] += 1
            
            # Diversity factor: reward bills with diverse submitters vs single organization spam
            if total_unique_submitters > 0:
                diversity_factor = min(total_unique_submitters / total_testimonies, 1.0) + 0.3
            else:
                diversity_factor = 0.3  # Minimum factor
            
            # Recency factor: boost recent testimony (using enhanced timeline data)
            recency_factor = 1.0 + (recent_testimonies / total_testimonies * 0.5)  # Up to 50% boost for recent activity
            
            # Calculate final hotness score
            hotness_score = total_testimonies * diversity_factor * recency_factor
            
            # Determine heat level
            if hotness_score >= 200:
                heat_level = "blazing"
                heat_emoji = "🔥"
            elif hotness_score >= 100:
                heat_level = "hot"
                heat_emoji = "🌶️"
            elif hotness_score >= 50:
                heat_level = "warm"
                heat_emoji = "🔶"
            else:
                heat_level = "mild"
                heat_emoji = "🟡"
            
            # Get bill title from Topic field (truncated)
            topic = first_testimony.get('Topic', '')
            title = topic[:100] + "..." if len(topic) > 100 else topic
            if not title:
                title = f"Legislative measure {bill_id}"
            
            # Get committee info
            committee_code = first_testimony.get('CommitteeCode', '')
            
            hot_bills_data.append({
                'bill_id': bill_id,
                'measure_prefix': measure_prefix,
                'measure_number': measure_number,
                'title': title,
                'committee': committee_code,
                'testimony_count': total_testimonies,
                'unique_organizations': unique_organizations,
                'unique_individuals': unique_individuals,
                'total_unique_submitters': total_unique_submitters,
                'recent_testimonies': recent_testimonies,
                'diversity_factor': round(diversity_factor, 2),
                'recency_factor': round(recency_factor, 2),
                'hotness_score': round(hotness_score, 1),
                'heat_level': heat_level,
                'heat_emoji': heat_emoji,
                
                # Enhanced breakdown data
                'position_breakdown': position_breakdown,
                'submitter_types': submitter_types,
                'top_submitters': top_submitters,
                'top_behalf_of': top_behalf_of,
                'timeline_breakdown': {
                    'recent_30_days': timeline_analysis['recent_30_days'],
                    'recent_90_days': timeline_analysis['recent_90_days'],
                    'this_year': timeline_analysis['this_year'],
                    'older': timeline_analysis['older']
                },
                'analysis_notes': {
                    'position_method': 'OLIS PositionOnMeasureId mapping (3981=neutral, 3982=in_favor, 3983=against)',
                    'data_quality': f'{position_breakdown["unknown"]}/{total_testimonies} testimonies have unknown/unmapped position IDs'
                }
            })
        
        # Sort by hotness score and limit results
        hot_bills_data.sort(key=lambda x: x['hotness_score'], reverse=True)
        top_hot_bills = hot_bills_data[:limit]
        
        return {
            'hot_bills': top_hot_bills,
            'total_testimonies': len(testimonies),
            'bills_with_testimony': len(bill_testimonies),
            'analysis_date': datetime.now().isoformat(),
            'methodology': {
                'formula': 'hotness_score = total_testimonies * diversity_factor * recency_factor',
                'diversity_factor': 'Based on unique organizations and individuals (0.3-1.3)',
                'recency_factor': 'Boost for testimony in last 30 days (1.0-1.5)'
            }
        }
        
    except Exception as e:
        # Return error info for debugging
        return {
            'hot_bills': [],
            'total_testimonies': 0,
            'bills_with_testimony': 0,
            'error': str(e),
            'analysis_date': datetime.now().isoformat()
        }

def get_heat_level_info(heat_level: str) -> Dict[str, str]:
    """Get display information for a heat level"""
    heat_info = {
        'blazing': {
            'emoji': '🔥',
            'color': 'red',
            'description': 'Extremely high testimony volume'
        },
        'hot': {
            'emoji': '🌶️', 
            'color': 'orange',
            'description': 'High testimony volume'
        },
        'warm': {
            'emoji': '🔶',
            'color': 'yellow',
            'description': 'Moderate testimony volume'
        },
        'mild': {
            'emoji': '🟡',
            'color': 'green',
            'description': 'Low testimony volume'
        }
    }
    
    return heat_info.get(heat_level, heat_info['mild'])