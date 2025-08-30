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
    'adult material', 'adult-oriented', 'adults-only','xnxx'
    
    # Adult Industry Terms
    'escort', 'adult dating', 'adult friend', 'hookup',
    'webcam', 'cam girl', 'live show', 'strip show',
    'strip chat', 'adult chat', 'adult meet', 'adult date',
    'sugar dating', 'sugar baby', 'sugar daddy',
    
    # Adult Content Descriptors
    'nude', 'naked', 'erotic', 'mature content',
    'sensual', 'seductive', 'intimate', 'sultry',
    'provocative', 'risque', 'uncensored', 'unrated',
    
    # Related Terms
    'bikini', 'lingerie', 'underwear', 'swimsuit',
    'massage parlor', 'adult spa', 'gentlemen club',
    'adult entertainment', 'adult service', 'adult venue',
    
    # Website Names and Terms
    'xvideos', 'pornhub', 'youporn', 'redtube', 'xhamster',
    'onlyfans', 'adult premium', 'adult subscription',
    
    # Arabic Keywords
    'جنس', 'اباحي', 'عاري', 'جماع', 'دعارة',
    'صور عارية', 'افلام للكبار', 'محتوى للبالغين',
    'مواقع اباحية', 'افلام اباحية', 'صور اباحية',
    
    # Additional Context Keywords
    'adult film', 'adult movie', 'adult video',
    'adult content', 'adults only', '18+', '21+',
    'not safe for work', 'age restricted', 'age verification',
    'adult verification', 'adult check', 'content warning',
    
    # Euphemisms and Indirect Terms
    'private show', 'private chat', 'exclusive content',
    'premium content', 'vip access', 'vip area',
    'members only', 'restricted area', 'adult zone',
    
    # Monetization Terms
    'adult payment', 'adult billing', 'discreet billing',
    'anonymous payment', 'crypto payment', 'token purchase'
]

# Suspicious URL patterns that might indicate adult content (using regex)
SUSPICIOUS_URL_PATTERNS = [
    # Content Type Patterns
    r'(?i)adult[-_]?content',
    r'(?i)xxx[-_]?videos?',
    r'(?i)porn[-_]?hub',
    r'(?i)sex[-_]?videos?',
    r'(?i)erotic[-_]?content',
    r'(?i)nsfw[-_]?content',
    r'(?i)mature[-_]?content',
    
    # Age Verification Patterns
    r'(?i)18[-_]?plus',
    r'(?i)21[-_]?plus',
    r'(?i)adults?[-_]?only',
    r'(?i)age[-_]?verify',
    r'(?i)age[-_]?verification',
    r'(?i)verify[-_]?age',
    
    # Adult Services Patterns
    r'(?i)adult[-_]?dating',
    r'(?i)adult[-_]?chat',
    r'(?i)adult[-_]?meet',
    r'(?i)escort[-_]?service',
    r'(?i)sugar[-_]?dating',
    
    # Content Access Patterns
    r'(?i)private[-_]?show',
    r'(?i)vip[-_]?access',
    r'(?i)members[-_]?area',
    r'(?i)premium[-_]?content',
    
    # Payment Related Patterns
    r'(?i)adult[-_]?billing',
    r'(?i)discreet[-_]?pay',
    r'(?i)token[-_]?purchase',
    
    # Streaming and Live Content
    r'(?i)live[-_]?cam',
    r'(?i)web[-_]?cam[-_]?show',
    r'(?i)strip[-_]?chat',
    
    # Common Obfuscation Patterns
    r'(?i)x{3,}',  # Matches 3 or more x's
    r'(?i)a[^a-z]?d[^a-z]?u[^a-z]?l[^a-z]?t',  # Matches "adult" with possible separators
    r'(?i)n[^a-z]?s[^a-z]?f[^a-z]?w',  # Matches "nsfw" with possible separators
    
    # URL Structure Patterns
    r'(?i)/adults?(?:/|$)',  # Matches /adult/ or /adults/ in URL paths
    r'(?i)/xxx(?:/|$)',      # Matches /xxx/ in URL paths
    r'(?i)/nsfw(?:/|$)',     # Matches /nsfw/ in URL paths
    
    # Query Parameter Patterns
    r'(?i)[?&]type=adult',
    r'(?i)[?&]content=mature',
    r'(?i)[?&]nsfw=(?:1|true|yes)'
]
