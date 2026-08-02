"""Closed vocabularies used by the Cortex Notify domain contract."""

from enum import StrEnum


class ActionType(StrEnum):
    """The permitted notification actions."""

    NOTIFY = "notify"
    DIGEST = "digest"
    MUTE = "mute"


class MessageType(StrEnum):
    """Semantic category assigned to a message by a later phase."""

    PERSONAL = "personal"
    URGENT = "urgent"
    EVENT = "event"
    PAYMENT = "payment"
    BUSINESS_UPDATE = "business_update"
    PROMOTION = "promotion"
    GREETING = "greeting"
    FORWARD = "forward"
    SPAM = "spam"
    SCAM = "scam"
    UNKNOWN = "unknown"


class MediaType(StrEnum):
    """Supported message media kinds."""

    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    DOCUMENT = "document"


class RelationshipType(StrEnum):
    """Relationship between a user and a sender or conversation."""

    SELF = "self"
    FAMILY = "family"
    FRIEND = "friend"
    COWORKER = "coworker"
    MANAGER = "manager"
    HR = "hr"
    DOCTOR = "doctor"
    CLOSE_FRIEND = "close_friend"
    FREQUENT_CONTACT = "frequent_contact"
    TRUSTED_CONTACT = "trusted_contact"
    BLOCKED_CONTACT = "blocked_contact"
    ADMIN = "admin"
    MEMBER = "member"
    UNKNOWN = "unknown"


class BusinessCategory(StrEnum):
    """Business account categories represented in the domain."""

    AIRLINE = "airline"
    BANK = "bank"
    BEAUTY = "beauty"
    CASHBACK_REWARDS = "cashback_rewards"
    CINEMA = "cinema"
    CLOUD_SECURITY = "cloud_security"
    CREDIT_CARD = "credit_card"
    ECOMMERCE = "ecommerce"
    ECOMMERCE_DELIVERY = "ecommerce_delivery"
    EDUCATION = "education"
    EVENTS = "events"
    FASHION = "fashion"
    FINANCE = "finance"
    FINTECH = "fintech"
    FITNESS_WELLNESS = "fitness_wellness"
    FOOD_DELIVERY = "food_delivery"
    GROCERY = "grocery"
    GROCERY_DELIVERY = "grocery_delivery"
    HEALTHCARE = "healthcare"
    HEALTHCARE_PRODUCT = "healthcare_product"
    HOME_SERVICES = "home_services"
    HOTEL = "hotel"
    INSURANCE = "insurance"
    LOGISTICS = "logistics"
    MARKETPLACE = "marketplace"
    PAYMENTS = "payments"
    QUICK_COMMERCE = "quick_commerce"
    REAL_ESTATE = "real_estate"
    RESTAURANT_DINING = "restaurant_dining"
    RETAIL = "retail"
    RIDE_BOOKING = "ride_booking"
    RIDES = "rides"
    SECURITY = "security"
    STREAMING = "streaming"
    TELECOM = "telecom"
    TRAFFIC_CHALLAN = "traffic_challan"
    TRAVEL = "travel"
    UTILITIES = "utilities"
    VEHICLE_INSURANCE = "vehicle_insurance"
    VEHICLE_SERVICE = "vehicle_service"
    DELIVERY = "delivery"
    SERVICES = "services"
    OTHER = "other"
    UNKNOWN = "unknown"


class ConversationType(StrEnum):
    """Supported WhatsApp conversation shapes."""

    PERSONAL = "personal"
    GROUP = "group"
    BUSINESS = "business"


class EvidenceType(StrEnum):
    """Sources from which a later phase may derive evidence."""

    HISTORICAL_MESSAGE = "historical_message"
    BEHAVIOR = "behavior"
    PREFERENCE = "preference"
    MEDIA = "media"
    METADATA = "metadata"
    RELATIONSHIP = "relationship"
    TOPIC = "topic"
    BUSINESS = "business"
    INTERACTION = "interaction"


class UrgencyLevel(StrEnum):
    """Human-readable urgency bands."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(StrEnum):
    """Human-readable risk bands."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SpamCategory(StrEnum):
    """Spam taxonomy for future deterministic feature extraction."""

    NONE = "none"
    PROMOTION = "promotion"
    REPETITIVE = "repetitive"
    UNSOLICITED = "unsolicited"
    SUSPICIOUS = "suspicious"
    UNKNOWN = "unknown"


class ValidationStatus(StrEnum):
    """Outcome of a validation boundary."""

    VALID = "valid"
    INVALID = "invalid"


class InteractionType(StrEnum):
    """Observed user interaction with a notification or message."""

    OPENED = "opened"
    REPLIED = "replied"
    DISMISSED = "dismissed"
    MUTED = "muted"
    REPORTED = "reported"
