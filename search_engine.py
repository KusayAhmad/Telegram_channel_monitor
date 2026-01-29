"""
Advanced Search Engine
Supports regular search and regex patterns
"""
import re
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from logger import monitor_logger


class MatchType(Enum):
    """Match type"""
    EXACT = "exact"           # Exact match
    CONTAINS = "contains"     # Contains
    STARTS_WITH = "starts"    # Starts with
    ENDS_WITH = "ends"        # Ends with
    REGEX = "regex"           # Regular expression
    CASE_SENSITIVE = "case"   # Case sensitive


@dataclass
class SearchPattern:
    """Search pattern"""
    pattern: str
    match_type: MatchType = MatchType.CONTAINS
    case_sensitive: bool = False
    compiled_regex: Optional[re.Pattern] = None
    
    def __post_init__(self):
        """Compile regex if necessary"""
        if self.match_type == MatchType.REGEX:
            try:
                flags = 0 if self.case_sensitive else re.IGNORECASE
                self.compiled_regex = re.compile(self.pattern, flags)
            except re.error as e:
                monitor_logger.error(f"Invalid regex '{self.pattern}': {e}")
                self.compiled_regex = None


@dataclass
class MatchResult:
    """Match result"""
    matched: bool
    pattern: str
    match_type: MatchType
    matched_text: Optional[str] = None
    position: Optional[Tuple[int, int]] = None
    
    def __bool__(self):
        return self.matched


class SearchEngine:
    """Advanced search engine"""
    
    def __init__(self):
        self.patterns: List[SearchPattern] = []
    
    def add_pattern(
        self, 
        pattern: str, 
        match_type: MatchType = MatchType.CONTAINS,
        case_sensitive: bool = False
    ):
        """Add search pattern"""
        search_pattern = SearchPattern(
            pattern=pattern,
            match_type=match_type,
            case_sensitive=case_sensitive
        )
        self.patterns.append(search_pattern)
        monitor_logger.debug(f"Pattern added: {pattern} ({match_type.value})")
    
    def add_regex(self, pattern: str, case_sensitive: bool = False):
        """Add regular expression"""
        self.add_pattern(pattern, MatchType.REGEX, case_sensitive)
    
    def add_keyword(self, keyword: str, case_sensitive: bool = False):
        """Add regular keyword"""
        self.add_pattern(keyword, MatchType.CONTAINS, case_sensitive)
    
    def clear_patterns(self):
        """Clear all patterns"""
        self.patterns.clear()
    
    def search(self, text: str) -> List[MatchResult]:
        """
        Search text for all patterns
        
        Returns:
            List of match results
        """
        if not text:
            return []
        
        results = []
        
        for pattern in self.patterns:
            result = self._match_pattern(text, pattern)
            if result.matched:
                results.append(result)
        
        return results
    
    def search_first(self, text: str) -> Optional[MatchResult]:
        """Search for first match only"""
        results = self.search(text)
        return results[0] if results else None
    
    def has_match(self, text: str) -> bool:
        """Check if any match exists"""
        return bool(self.search_first(text))
    
    def _match_pattern(self, text: str, pattern: SearchPattern) -> MatchResult:
        """Apply pattern to text"""
        search_text = text if pattern.case_sensitive else text.lower()
        search_pattern = pattern.pattern if pattern.case_sensitive else pattern.pattern.lower()
        
        matched = False
        matched_text = None
        position = None
        
        if pattern.match_type == MatchType.REGEX:
            if pattern.compiled_regex:
                match = pattern.compiled_regex.search(text)
                if match:
                    matched = True
                    matched_text = match.group()
                    position = match.span()
        
        elif pattern.match_type == MatchType.EXACT:
            matched = search_text == search_pattern
            if matched:
                matched_text = text
                position = (0, len(text))
        
        elif pattern.match_type == MatchType.CONTAINS:
            idx = search_text.find(search_pattern)
            if idx != -1:
                matched = True
                matched_text = text[idx:idx + len(pattern.pattern)]
                position = (idx, idx + len(pattern.pattern))
        
        elif pattern.match_type == MatchType.STARTS_WITH:
            if search_text.startswith(search_pattern):
                matched = True
                matched_text = text[:len(pattern.pattern)]
                position = (0, len(pattern.pattern))
        
        elif pattern.match_type == MatchType.ENDS_WITH:
            if search_text.endswith(search_pattern):
                matched = True
                matched_text = text[-len(pattern.pattern):]
                position = (len(text) - len(pattern.pattern), len(text))
        
        return MatchResult(
            matched=matched,
            pattern=pattern.pattern,
            match_type=pattern.match_type,
            matched_text=matched_text,
            position=position
        )
    
    @staticmethod
    def create_from_keywords(
        keywords: List[str], 
        regex_patterns: List[str] = None
    ) -> 'SearchEngine':
        """
        Create search engine from word list
        
        Args:
            keywords: Regular keywords
            regex_patterns: Regular expressions
        """
        engine = SearchEngine()
        
        for keyword in keywords:
            engine.add_keyword(keyword)
        
        if regex_patterns:
            for pattern in regex_patterns:
                engine.add_regex(pattern)
        
        return engine


class AdvancedPatterns:
    """Ready-made advanced search patterns"""
    
    # Price patterns
    PRICE_USD = r'\$\d+(?:\.\d{2})?'
    PRICE_EUR = r'€\d+(?:\.\d{2})?'
    PRICE_ANY = r'[\$€£¥]\d+(?:\.\d{2})?'
    
    # Link patterns
    URL = r'https?://[^\s<>"{}|\\^`\[\]]+'
    TELEGRAM_LINK = r't\.me/[a-zA-Z0-9_]+'
    AMAZON_LINK = r'amazon\.[a-z.]+/[^\s]+'
    
    # Discount patterns
    DISCOUNT_PERCENT = r'\d+%\s*(off|خصم|discount)?'
    DISCOUNT_CODE = r'(code|كود|coupon)[\s:]*[A-Z0-9]+'
    
    # Date patterns
    DATE_DMY = r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}'
    DATE_YMD = r'\d{4}[/\-]\d{1,2}[/\-]\d{1,2}'
    
    # Number patterns
    PHONE_INTL = r'\+\d{1,3}[\s\-]?\d{6,14}'
    DIGITS = r'\d+'
    
    @classmethod
    def get_ecommerce_patterns(cls) -> List[str]:
        """E-commerce patterns"""
        return [
            cls.PRICE_ANY,
            cls.DISCOUNT_PERCENT,
            cls.DISCOUNT_CODE,
            cls.AMAZON_LINK
        ]
    
    @classmethod
    def get_link_patterns(cls) -> List[str]:
        """Link patterns"""
        return [
            cls.URL,
            cls.TELEGRAM_LINK
        ]


def parse_keyword_string(keyword_str: str) -> Tuple[str, MatchType, bool]:
    """
    Parse keyword string with options
    
    Format: [type:]keyword[:sensitive]
    Examples:
        - "test" -> regular
        - "regex:test.*" -> regular expression
        - "exact:test:cs" -> exact match, case sensitive
    """
    parts = keyword_str.split(':')
    
    keyword = keyword_str
    match_type = MatchType.CONTAINS
    case_sensitive = False
    
    if len(parts) >= 2:
        type_map = {
            'regex': MatchType.REGEX,
            'exact': MatchType.EXACT,
            'starts': MatchType.STARTS_WITH,
            'ends': MatchType.ENDS_WITH,
            'contains': MatchType.CONTAINS
        }
        
        if parts[0].lower() in type_map:
            match_type = type_map[parts[0].lower()]
            keyword = ':'.join(parts[1:])
        
        if len(parts) >= 3 and parts[-1].lower() in ['cs', 'case']:
            case_sensitive = True
            keyword = ':'.join(parts[1:-1])
    
    return keyword, match_type, case_sensitive
