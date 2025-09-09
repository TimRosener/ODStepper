"""
Oregon Legislative Committee Code Mapping
Maps OLIS committee codes to readable names and organizes by chamber
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CommitteeInfo:
    """Information about a legislative committee"""
    full_name: str
    chamber: str  # 'house', 'senate', 'joint'
    short_name: str
    description: str

# Oregon Legislative Committee Code Mappings
# Based on OLIS CurrentCommitteeCode field analysis
COMMITTEE_MAPPINGS: Dict[str, CommitteeInfo] = {
    # House Committees
    'HRULES': CommitteeInfo(
        full_name='House Rules Committee',
        chamber='house',
        short_name='Rules',
        description='House committee that manages legislative rules and procedures'
    ),
    'HED': CommitteeInfo(
        full_name='House Education Committee',
        chamber='house', 
        short_name='Education',
        description='House committee overseeing education policy'
    ),
    'HALNRW': CommitteeInfo(
        full_name='House Agriculture, Land Use, Natural Resources, and Water Committee',
        chamber='house',
        short_name='Agriculture & Natural Resources',
        description='House committee for agriculture and natural resource issues'
    ),
    'HEMGGV': CommitteeInfo(
        full_name='House Emergency Management, General Government, and Veterans Committee',
        chamber='house',
        short_name='Emergency Management & Veterans',
        description='House committee for emergency management and veteran affairs'
    ),
    'HCEE': CommitteeInfo(
        full_name='House Committee on Economic Development and Small Business',
        chamber='house',
        short_name='Economic Development',
        description='House committee for economic development and small business'
    ),
    'HCOND': CommitteeInfo(
        full_name='House Committee on Conduct',
        chamber='house',
        short_name='Conduct',
        description='House ethics and conduct committee'
    ),
    'HJUD': CommitteeInfo(
        full_name='House Judiciary Committee',
        chamber='house',
        short_name='Judiciary',
        description='House committee for judicial and legal matters'
    ),
    'HBHHC': CommitteeInfo(
        full_name='House Behavioral Health and Health Care Committee',
        chamber='house',
        short_name='Behavioral Health & Health Care',
        description='House committee for behavioral health and healthcare policy'
    ),
    'HREV': CommitteeInfo(
        full_name='House Revenue Committee',
        chamber='house',
        short_name='Revenue',
        description='House committee for taxation and revenue matters'
    ),
    'HLWS': CommitteeInfo(
        full_name='House Labor and Workforce Systems Committee',
        chamber='house',
        short_name='Labor & Workforce Systems',
        description='House committee for labor and workforce issues'
    ),
    'HHOUSH': CommitteeInfo(
        full_name='House Housing and Homelessness Committee',
        chamber='house',
        short_name='Housing & Homelessness',
        description='House committee for housing and homelessness policy'
    ),
    'HECDSB': CommitteeInfo(
        full_name='House Early Childhood Development and School-Based Programs Committee',
        chamber='house',
        short_name='Early Childhood & School Programs',
        description='House committee for early childhood and school-based programs'
    ),
    'HCCP': CommitteeInfo(
        full_name='House Climate, Communications, and Public Utilities Committee',
        chamber='house',
        short_name='Climate & Communications',
        description='House committee for climate, communications, and public utilities'
    ),
    'HHED': CommitteeInfo(
        full_name='House Higher Education Committee',
        chamber='house',
        short_name='Higher Education',
        description='House committee for higher education policy'
    ),
    'HECHS': CommitteeInfo(
        full_name='House Ethics Committee',
        chamber='house',
        short_name='Ethics',
        description='House committee for ethics and standards'
    ),
    
    # Senate Committees  
    'SRULES': CommitteeInfo(
        full_name='Senate Rules Committee',
        chamber='senate',
        short_name='Rules',
        description='Senate committee that manages legislative rules and procedures'
    ),
    'SHC': CommitteeInfo(
        full_name='Senate Health Care Committee',
        chamber='senate',
        short_name='Health Care',
        description='Senate committee overseeing health care policy'
    ),
    'SLB': CommitteeInfo(
        full_name='Senate Labor and Business Committee',
        chamber='senate',
        short_name='Labor & Business',
        description='Senate committee for labor and business issues'
    ),
    'SJUD': CommitteeInfo(
        full_name='Senate Judiciary Committee',
        chamber='senate',
        short_name='Judiciary',
        description='Senate committee for judicial and legal matters'
    ),
    'SEE': CommitteeInfo(
        full_name='Senate Environment and Energy Committee',
        chamber='senate',
        short_name='Environment & Energy',
        description='Senate committee for environmental and energy policy'
    ),
    'SNRW': CommitteeInfo(
        full_name='Senate Natural Resources and Wildfire Recovery Committee',
        chamber='senate',
        short_name='Natural Resources & Wildfire',
        description='Senate committee for natural resources and wildfire issues'
    ),
    'SFR': CommitteeInfo(
        full_name='Senate Finance and Revenue Committee',
        chamber='senate',
        short_name='Finance & Revenue',
        description='Senate committee for fiscal and revenue matters'
    ),
    'SVEMFW': CommitteeInfo(
        full_name='Senate Veterans, Emergency Management, Federal, and World Affairs Committee',
        chamber='senate',
        short_name='Veterans & Emergency Management',
        description='Senate committee for veterans and emergency management'
    ),
    'SED': CommitteeInfo(
        full_name='Senate Education Committee',
        chamber='senate',
        short_name='Education',
        description='Senate committee overseeing education policy'
    ),
    'SHS': CommitteeInfo(
        full_name='Senate Housing and Development Committee',
        chamber='senate',
        short_name='Housing & Development',
        description='Senate committee for housing and development issues'
    ),
    'SHDEV': CommitteeInfo(
        full_name='Senate Human Development Committee',
        chamber='senate',
        short_name='Human Development',
        description='Senate committee for human development and social services'
    ),
    'SECBH': CommitteeInfo(
        full_name='Senate Early Childhood and Behavioral Health Committee',
        chamber='senate',
        short_name='Early Childhood & Behavioral Health',
        description='Senate committee for early childhood and behavioral health issues'
    ),
    
    # Joint Committees
    'JWM': CommitteeInfo(
        full_name='Joint Committee on Ways and Means',
        chamber='joint',
        short_name='Ways & Means',
        description='Joint committee responsible for state budget and appropriations'
    ),
    'JCT': CommitteeInfo(
        full_name='Joint Committee on Carbon Reduction',
        chamber='joint',
        short_name='Carbon Reduction',
        description='Joint committee focused on carbon reduction policies'
    ),
    'JACSR': CommitteeInfo(
        full_name='Joint Committee on Addiction and Community Safety Response',
        chamber='joint',
        short_name='Addiction & Community Safety',
        description='Joint committee addressing addiction and community safety'
    ),
    'JLCIMT': CommitteeInfo(
        full_name='Joint Legislative Committee on Information Management and Technology',
        chamber='joint',
        short_name='Information Management & Technology',
        description='Joint committee overseeing legislative technology'
    ),
    'JCTE': CommitteeInfo(
        full_name='Joint Committee on Transportation and Economic Development',
        chamber='joint',
        short_name='Transportation & Economic Development',
        description='Joint committee for transportation and economic development'
    ),
    'JLAUD': CommitteeInfo(
        full_name='Joint Legislative Audit Committee',
        chamber='joint',
        short_name='Legislative Audit',
        description='Joint committee for legislative auditing and oversight'
    ),
    'JTR': CommitteeInfo(
        full_name='Joint Committee on Transportation',
        chamber='joint',
        short_name='Transportation',
        description='Joint committee for transportation policy and infrastructure'
    ),
}

def get_committee_info(committee_code: str) -> Optional[CommitteeInfo]:
    """
    Get committee information for a given committee code
    
    Args:
        committee_code: OLIS committee code (e.g., 'HRULES', 'SHC', 'JWM')
        
    Returns:
        CommitteeInfo object if code is found, None otherwise
    """
    return COMMITTEE_MAPPINGS.get(committee_code)

def get_committees_by_chamber() -> Dict[str, Dict[str, CommitteeInfo]]:
    """
    Get all committees organized by chamber
    
    Returns:
        Dictionary with 'house', 'senate', 'joint' keys containing committee mappings
    """
    chambers = {'house': {}, 'senate': {}, 'joint': {}}
    
    for code, info in COMMITTEE_MAPPINGS.items():
        chambers[info.chamber][code] = info
    
    return chambers

def is_valid_committee_code(committee_code: str) -> bool:
    """
    Check if a committee code is valid/recognized
    
    Args:
        committee_code: Committee code to validate
        
    Returns:
        True if valid, False otherwise
    """
    return committee_code in COMMITTEE_MAPPINGS

def get_committee_display_name(committee_code: str, use_short_name: bool = True) -> str:
    """
    Get display name for a committee
    
    Args:
        committee_code: OLIS committee code
        use_short_name: If True, use short name; if False, use full name
        
    Returns:
        Committee display name, or the original code if not found
    """
    info = get_committee_info(committee_code)
    if info:
        return info.short_name if use_short_name else info.full_name
    return committee_code  # Fallback to original code if not mapped