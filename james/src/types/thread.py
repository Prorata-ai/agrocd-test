from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class UserType(str, Enum):
    PRO_RATA_INTERNAL = "ProRataInternal"
    PARTNER_PILOT = "PartnerPilot"
    PARTNER_DOMAIN = "PartnerDomain"
    INTERNAL_TEST_USER = "InternalTestUser"
    GUEST_USER = "GuestUser"
    LOGGED_IN_USER = "LoggedInUser"


class EntryPoint(str, Enum):
    GIST_HOME_PAGE = "GistHomePage"
    GIST_NEW_QUESTION = "GistNewQuestion"
    GIST_TILE = "GistTile"
    GIST_SHARED = "GistShared"
    GIST_AD_CAMPAIGN = "GistAdCampaign"
    PARTNER_SEARCH_BOX = "PartnerSearchBox"
    PARTNER_SUMMARY = "PartnerSummary"
    PARTNER_TILE = "PartnerTile"
    PARTNER_SHARED = "PartnerShared"
    OTHER = "Other"


@dataclass
class ThreadEvent:
    """
    Represents a thread event as defined in the ClickHouse thread_events table.
    
    Fields match the columns in the thread_events table.
    """
    thread_id: str
    created_at: datetime
    user_id: str
    user_type: UserType
    user_partner_id: Optional[str] = ""
    entry_point: EntryPoint = EntryPoint.OTHER
    ad_campaign_id: Optional[str] = ""
    channel_partner_id: Optional[str] = ""
    tile_id: Optional[str] = ""
    tile_prompt: Optional[str] = ""
    
    def to_dict(self):
        """Convert the dataclass to a dictionary for database insertion"""
        return {
            "thread_id": self.thread_id,
            "created_at": self.created_at,
            "user_id": self.user_id,
            "user_type": self.user_type,
            "user_partner_id": self.user_partner_id or "",
            "entry_point": self.entry_point,
            "ad_campaign_id": self.ad_campaign_id or "",
            "channel_partner_id": self.channel_partner_id or "",
            "tile_id": self.tile_id or "",
            "tile_prompt": self.tile_prompt or ""
        } 