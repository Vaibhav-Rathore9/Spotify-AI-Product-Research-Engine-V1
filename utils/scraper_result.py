"""
ScraperResult dataclass for standardized scraper outputs.

Every scraper should return a ScraperResult object that provides
transparent information about the scraping operation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ScraperResult:
    """Standardized result from any scraper operation."""
    
    success: bool
    source: str
    review_count: int
    used_cache: bool
    error: Optional[str]
    reviews: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "source": self.source,
            "review_count": self.review_count,
            "used_cache": self.used_cache,
            "error": self.error,
            "reviews": self.reviews
        }
    
    @classmethod
    def success_result(cls, source: str, reviews: List[Dict[str, Any]], used_cache: bool = False) -> 'ScraperResult':
        """Create a successful result."""
        return cls(
            success=True,
            source=source,
            review_count=len(reviews),
            used_cache=used_cache,
            error=None,
            reviews=reviews
        )
    
    @classmethod
    def failure_result(cls, source: str, error: str, used_cache: bool = False, 
                      cached_reviews: List[Dict[str, Any]] = None) -> 'ScraperResult':
        """Create a failure result."""
        return cls(
            success=False,
            source=source,
            review_count=0 if not cached_reviews else len(cached_reviews),
            used_cache=used_cache,
            error=error,
            reviews=cached_reviews or []
        )