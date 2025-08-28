"""
Configuration file containing filters for adult content detection
"""

# Known adult domains that should be blocked immediately
ADULT_DOMAINS = [
    'pornhub.com', 'xvideos.com', 'xnxx.com', 'redtube.com', 
    'youporn.com', 'xhamster.com', 'tube8.com', 'youjizz.com',
    'spankbang.com', 'cam4.com', 'chaturbate.com', 'myfreecams.com',
    'livejasmin.com', 'stripchat.com', 'bongacams.com', 'onlyfans.com',
    'adultwork.com', 'seeking.com', 'adultfriendfinder.com',
    'beeg.com', 'tnaflix.com', 'drtuber.com', 'porn.com', 'sex.com',
    'brazzers.com', 'bangbros.com'
]

# Extended list of adult content keywords
ADULT_KEYWORDS = [
    # Explicit Content Keywords
    'porn', 'xxx', 'adult content', 'nsfw', 'explicit',
    
    # Adult Industry Terms
    'escort', 'adult dating', 'adult friend', 'hookup',
    'webcam', 'cam girl', 'live show',
    
    # Adult Content Descriptors
    'nude', 'naked', 'erotic', 'mature content',
    'sensual', 'seductive', 'intimate', 'sultry',
    
    # Related Terms
    'bikini', 'lingerie', 'underwear',
    'massage parlor', 'adult spa',
    
    # Website Names
    'xvideos', 'pornhub', 'youporn', 'redtube', 'xhamster',
    
    # Arabic Keywords
    'جنس', 'اباحي', 'عاري', 'جماع', 'دعارة',
    'صور عارية', 'افلام للكبار', 'محتوى للبالغين',
    
    # Additional Context Keywords
    'adult film', 'adult movie', 'adult video',
    'adult content', 'adults only', '18+',
    'not safe for work', 'age restricted'
]

# Suspicious URL patterns that might indicate adult content (using regex)
SUSPICIOUS_URL_PATTERNS = [
    r'(?i)adult[-_]?content',
    r'(?i)xxx[-_]?videos?',
    r'(?i)porn[-_]?hub',
    r'(?i)sex[-_]?videos?',
    r'(?i)erotic[-_]?content',
    r'(?i)nsfw[-_]?content',
    r'(?i)mature[-_]?content',
    r'(?i)18[-_]?plus',
    r'(?i)adults?[-_]?only',
    r'(?i)adult[-_]?dating'
]
