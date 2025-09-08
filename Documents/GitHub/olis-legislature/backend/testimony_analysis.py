"""
Hot Bills Analysis based on testimony volume and diversity
"""

from typing import Dict, Any, List
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import math

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
            
            # Calculate metrics
            total_testimonies = len(bill_testimonies_list)
            
            # Calculate organizational diversity
            organizations = set()
            individuals = set()
            
            for testimony in bill_testimonies_list:
                org = testimony.get('Organization', '').strip()
                name = f"{testimony.get('SubmitterFirstName', '')} {testimony.get('SubmitterLastName', '')}".strip()
                
                if org and org.lower() not in ['n/a', 'none', 'individual']:
                    organizations.add(org.lower())
                elif name:
                    individuals.add(name.lower())
            
            unique_organizations = len(organizations)
            unique_individuals = len(individuals)
            total_unique_submitters = unique_organizations + unique_individuals
            
            # Diversity factor: reward bills with diverse submitters vs single organization spam
            if total_unique_submitters > 0:
                diversity_factor = min(total_unique_submitters / total_testimonies, 1.0) + 0.3
            else:
                diversity_factor = 0.3  # Minimum factor
            
            # Recency factor: boost recent testimony
            recent_date = datetime.now() - timedelta(days=30)
            recent_testimonies = 0
            
            for testimony in bill_testimonies_list:
                meeting_date_str = testimony.get('MeetingDate', '')
                if meeting_date_str:
                    try:
                        meeting_date = datetime.fromisoformat(meeting_date_str.replace('T', ' ').replace('Z', ''))
                        if meeting_date > recent_date:
                            recent_testimonies += 1
                    except:
                        pass  # Skip if date parsing fails
            
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
                'heat_emoji': heat_emoji
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