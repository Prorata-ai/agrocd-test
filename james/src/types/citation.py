from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Tuple
import os
import sys

# Add the src directory to the path so we can import the ClickHouse client
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from clients.clickhouse_client import ClickHouseClient


@dataclass
class CitationEvent:
    """
    Represents a citation event as defined in the ClickHouse citation_events table.
    
    Fields match the columns in the citation_events table.
    """
    turn_id: int
    thread_id: str
    user_id: str
    domain: str
    url: str
    title: str
    attribution_score: int
    attribution_rank: int
    response_time: datetime
    publisher_id: Optional[str] = ""
    was_clicked: bool = False
    location_country: Optional[str] = ""
    location_region: Optional[str] = ""
    location_city: Optional[str] = ""
    ingestion_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Set default value for ingestion_time if not provided"""
        if self.ingestion_time is None:
            self.ingestion_time = datetime.now()
    
    def to_dict(self):
        """Convert the dataclass to a dictionary for database insertion"""
        return {
            "turn_id": self.turn_id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "domain": self.domain,
            "url": self.url,
            "title": self.title,
            "publisher_id": self.publisher_id or "",
            "attribution_score": self.attribution_score,
            "attribution_rank": self.attribution_rank,
            "was_clicked": self.was_clicked,
            "response_time": self.response_time,
            "location_country": self.location_country or "",
            "location_region": self.location_region or "",
            "location_city": self.location_city or "",
            "ingestion_time": self.ingestion_time
        }

    @classmethod
    def _get_client(cls) -> ClickHouseClient:
        """Get a ClickHouse client instance"""
        client = ClickHouseClient(
            url=os.getenv("CLICKHOUSE_URL"),
            user=os.getenv("CLICKHOUSE_USERNAME"),
            password=os.getenv("CLICKHOUSE_PASSWORD"),
            database=os.getenv("CLICKHOUSE_DATABASE")
        )
        client.connect()
        return client

    @classmethod
    def get_count_for_turn(cls, thread_id: str, turn_index: int) -> int:
        """Get citation count for a specific turn"""
        client = cls._get_client()
        try:
            result = client.execute_query(f"""
            SELECT count() 
            FROM citation_events 
            WHERE thread_id = '{thread_id}' AND turn_id = {turn_index}
            """)
            return result[0][0]
        finally:
            client.close()

    @classmethod
    def get_citations_for_turn(cls, thread_id: str, turn_index: int) -> List[Tuple]:
        """Get citations for a specific turn"""
        client = cls._get_client()
        try:
            return client.execute_query(f"""
            SELECT 
                domain,
                url,
                title,
                attribution_score,
                attribution_rank,
                was_clicked
            FROM citation_events 
            WHERE thread_id = '{thread_id}' AND turn_id = {turn_index}
            ORDER BY attribution_rank
            """)
        finally:
            client.close()

    @classmethod
    def get_citation_counts_batch(cls, turn_data: List[Tuple[str, int]]) -> dict:
        """Get citation counts for multiple turns in a single query"""
        if not turn_data:
            return {}
            
        client = cls._get_client()
        try:
            # Build WHERE clause for multiple thread_id/turn_id combinations
            conditions = []
            for thread_id, turn_index in turn_data:
                conditions.append(f"(thread_id = '{thread_id}' AND turn_id = {turn_index})")
            
            where_clause = " OR ".join(conditions)
            
            result = client.execute_query(f"""
            SELECT 
                thread_id,
                turn_id,
                count() as citation_count
            FROM citation_events 
            WHERE {where_clause}
            GROUP BY thread_id, turn_id
            """)
            
            # Convert to dictionary for easy lookup
            citation_counts = {}
            for thread_id, turn_id, count in result:
                citation_counts[(thread_id, turn_id)] = count
                
            return citation_counts
        finally:
            client.close()

    @classmethod
    def get_citations_batch(cls, turn_data: List[Tuple[str, int]]) -> dict:
        """Get citation details for multiple turns in a single query"""
        if not turn_data:
            return {}
            
        client = cls._get_client()
        try:
            # Build WHERE clause for multiple thread_id/turn_id combinations
            conditions = []
            for thread_id, turn_index in turn_data:
                conditions.append(f"(thread_id = '{thread_id}' AND turn_id = {turn_index})")
            
            where_clause = " OR ".join(conditions)
            
            result = client.execute_query(f"""
            SELECT 
                thread_id,
                turn_id,
                domain,
                url,
                title,
                attribution_score,
                attribution_rank,
                was_clicked
            FROM citation_events 
            WHERE {where_clause}
            ORDER BY thread_id, turn_id, attribution_rank
            """)
            
            # Group results by (thread_id, turn_id)
            citation_details = {}
            for row in result:
                thread_id, turn_id = row[0], row[1]
                citation_data = row[2:]  # domain, url, title, score, rank, clicked
                
                key = (thread_id, turn_id)
                if key not in citation_details:
                    citation_details[key] = []
                citation_details[key].append(citation_data)
                
            return citation_details
        finally:
            client.close() 