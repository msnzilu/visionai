# backend/app/models/common.py
"""
Common Pydantic models and base classes used across the application
"""

from pydantic import BaseModel as PydanticBaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union, Generic, TypeVar
from datetime import datetime
from enum import Enum
import re

# Generic type for paginated responses
T = TypeVar('T')


class BaseModel(PydanticBaseModel):
    """Base model with common configuration"""
    
    class Config:
        # Allow population by field name or alias
        populate_by_name = True
        # Use enum values instead of enum names
        use_enum_values = True
        # JSON encoders for special types
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        # Validate assignment
        validate_assignment = True


class TimeStampedModel(BaseModel):
    """Model with timestamp fields"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SoftDeleteModel(TimeStampedModel):
    """Model with soft delete capability"""
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None


# Response Models
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseResponse):
    """Success response model"""
    data: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool
    
    @validator('pages', always=True)
    def calculate_pages(cls, v, values):
        total = values.get('total', 0)
        size = values.get('size', 20)
        return (total + size - 1) // size if size > 0 else 0
    
    @validator('has_next', always=True)
    def calculate_has_next(cls, v, values):
        page = values.get('page', 1)
        pages = values.get('pages', 0)
        return page < pages
    
    @validator('has_prev', always=True)
    def calculate_has_prev(cls, v, values):
        page = values.get('page', 1)
        return page > 1


# File Upload Models
class FileInfo(BaseModel):
    """File information model"""
    filename: str
    content_type: str
    size: int
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('filename')
    def validate_filename(cls, v):
        # Remove path components and dangerous characters
        filename = v.split('/')[-1].split('\\')[-1]
        # Replace dangerous characters
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        if not filename:
            raise ValueError("Invalid filename")
        return filename


class FileUploadResponse(BaseModel):
    """File upload response model"""
    file_id: str
    filename: str
    file_path: str
    size: int
    content_type: str
    upload_date: datetime
    url: Optional[str] = None


# Search and Filter Models
class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SortBy(BaseModel):
    """Sort specification model"""
    field: str
    order: SortOrder = SortOrder.ASC


class FilterOperator(str, Enum):
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    IN = "in"
    NOT_IN = "nin"
    CONTAINS = "contains"
    STARTS_WITH = "startswith"
    ENDS_WITH = "endswith"
    REGEX = "regex"


class FilterCondition(BaseModel):
    """Filter condition model"""
    field: str
    operator: FilterOperator
    value: Union[str, int, float, bool, List[Any]]


class SearchQuery(BaseModel):
    """Search query model"""
    query: Optional[str] = None
    filters: List[FilterCondition] = []
    sort: List[SortBy] = []
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


# Geographic Models
class Coordinates(BaseModel):
    """Geographic coordinates model"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class Address(BaseModel):
    """Address model"""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str
    postal_code: Optional[str] = None
    coordinates: Optional[Coordinates] = None


# Contact Information Models
class ContactInfo(BaseModel):
    """Contact information model"""
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    
    @validator('email')
    def validate_email(cls, v):
        if v:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError("Invalid email format")
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            # Remove spaces, dashes, parentheses
            phone = re.sub(r'[\s\-\(\)]', '', v)
            # Check if it's a valid phone number (basic validation)
            if not re.match(r'^\+?[\d]{7,15}$', phone):
                raise ValueError("Invalid phone number format")
        return v


# Money and Currency Models
class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"


class Money(BaseModel):
    """Money amount with currency"""
    amount: float = Field(..., ge=0)
    currency: Currency = Currency.USD
    
    def __str__(self):
        return f"{self.amount:.2f} {self.currency}"


# Status and Priority Enums
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    DELETED = "deleted"


# Notification Models
class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationPreference(BaseModel):
    """Notification preference model"""
    type: NotificationType
    enabled: bool = True
    frequency: str = "immediate"  # immediate, daily, weekly


# API Key and Authentication Models
class APIKeyInfo(BaseModel):
    """API key information model"""
    key_id: str
    name: str
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True
    permissions: List[str] = []


# Analytics and Statistics Models
class DateRange(BaseModel):
    """Date range model"""
    start_date: datetime
    end_date: datetime
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        start_date = values.get('start_date')
        if start_date and v <= start_date:
            raise ValueError("End date must be after start date")
        return v


class MetricValue(BaseModel):
    """Metric value model"""
    name: str
    value: Union[int, float]
    unit: Optional[str] = None
    description: Optional[str] = None


class TimeSeriesPoint(BaseModel):
    """Time series data point"""
    timestamp: datetime
    value: Union[int, float]
    metadata: Optional[Dict[str, Any]] = None


class AnalyticsData(BaseModel):
    """Analytics data model"""
    metrics: List[MetricValue]
    time_series: List[TimeSeriesPoint] = []
    date_range: DateRange
    filters: Optional[Dict[str, Any]] = None


# Configuration Models
class Feature(BaseModel):
    """Feature flag model"""
    name: str
    enabled: bool = True
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class SystemConfig(BaseModel):
    """System configuration model"""
    features: List[Feature] = []
    settings: Dict[str, Any] = {}
    version: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Webhook Models
class WebhookEvent(BaseModel):
    """Webhook event model"""
    event_type: str
    event_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]
    source: str


class WebhookEndpoint(BaseModel):
    """Webhook endpoint model"""
    url: str
    events: List[str]
    active: bool = True
    secret: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


# Health Check Models
class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceHealth(BaseModel):
    """Service health model"""
    service: str
    status: HealthStatus
    response_time: Optional[float] = None
    last_check: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None


class HealthCheck(BaseModel):
    """Overall health check model"""
    status: HealthStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: List[ServiceHealth] = []
    version: str


# Rate Limiting Models
class RateLimit(BaseModel):
    """Rate limit configuration"""
    requests: int = 100
    period: int = 3600  # seconds
    burst: int = 10


class RateLimitStatus(BaseModel):
    """Rate limit status"""
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None