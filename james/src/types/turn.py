from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Tuple
import os
import sys

# Add the src directory to the path so we can import the ClickHouse client
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from clients.clickhouse_client import ClickHouseClient


class ResponseType(str, Enum):
    BLOCKED_BY_GUARDRAIL = "BlockedByGuardrail"
    NO_RAG_RETURNED = "NoRAGReturned"
    ANSWER_BUT_NO_CITATIONS = "AnswerButNoCitations"
    ANSWER_WITH_CITATIONS = "AnswerWithCitations"
    UNKNOWN = "Unknown"
    OTHER = "Other"


@dataclass
class TurnEvent:
    """
    Represents a turn event as defined in the ClickHouse turn_events table.
    
    Fields match the columns in the turn_events table.
    """
    thread_id: str
    turn_index: int
    user_id: str
    redacted_user_prompt_text: str
    created_at: datetime
    response_length: int
    response_type: ResponseType = ResponseType.UNKNOWN
    redacted_condensed_prompt_text: Optional[str] = ""
    inference_model_used: Optional[str] = ""
    tokens_used: int = 0
    guardrail_id: Optional[str] = ""
    response_num_sections: int = 0
    response_has_markdown_list: bool = False
    response_has_markdown_table: bool = False
    time_to_first_token_ms: int = 0
    time_to_full_response_ms: int = 0
    time_related_qs_ms: int = 0
    time_attribution_ms: int = 0
    consumer_intent_class: Optional[str] = ""
    iab_class: Optional[str] = ""
    
    def to_dict(self):
        """Convert the dataclass to a dictionary for database insertion"""
        return {
            "thread_id": self.thread_id,
            "turn_index": self.turn_index,
            "user_id": self.user_id,
            "redacted_user_prompt_text": self.redacted_user_prompt_text,
            "redacted_condensed_prompt_text": self.redacted_condensed_prompt_text or "",
            "created_at": self.created_at,
            "inference_model_used": self.inference_model_used or "",
            "tokens_used": self.tokens_used,
            "response_length": self.response_length,
            "response_type": self.response_type,
            "guardrail_id": self.guardrail_id or "",
            "response_num_sections": self.response_num_sections,
            "response_has_markdown_list": self.response_has_markdown_list,
            "response_has_markdown_table": self.response_has_markdown_table,
            "time_to_first_token_ms": self.time_to_first_token_ms,
            "time_to_full_response_ms": self.time_to_full_response_ms,
            "time_related_qs_ms": self.time_related_qs_ms,
            "time_attribution_ms": self.time_attribution_ms,
            "consumer_intent_class": self.consumer_intent_class or "",
            "iab_class": self.iab_class or ""
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
    def get_count(cls) -> int:
        """Get total count of turns in the database"""
        client = cls._get_client()
        try:
            result = client.execute_query("SELECT count() FROM turn_events")
            return result[0][0]
        finally:
            client.close()

    @classmethod
    def get_turns_data(cls, limit: int = 50, offset: int = 0, date_filter: Optional[datetime] = None) -> List[Tuple]:
        """Get turns data with pagination and optional date filter"""
        client = cls._get_client()
        try:
            date_condition = ""
            if date_filter:
                # Format datetime for ClickHouse compatibility
                formatted_date = date_filter.strftime('%Y-%m-%d %H:%M:%S')
                date_condition = f"WHERE created_at >= '{formatted_date}'"
            
            query = f"""
            SELECT 
                te.thread_id,
                te.turn_index,
                te.created_at,
                te.user_id,
                te.redacted_user_prompt_text,
                te.response_length,
                te.response_type,
                te.response_has_markdown_list,
                te.response_has_markdown_table,
                te.time_to_full_response_ms,
                thr.tile_prompt as thread_title
            FROM turn_events te
            LEFT JOIN thread_events thr ON te.thread_id = thr.thread_id
            {date_condition}
            ORDER BY te.created_at DESC
            LIMIT {limit} OFFSET {offset}
            """
            
            return client.execute_query(query)
        finally:
            client.close()

    @classmethod
    def get_daily_count(cls, days: int = 30, date_filter: Optional[datetime] = None) -> List[Tuple]:
        """Get count of turns by day for the last N days or from a specific date"""
        client = cls._get_client()
        try:
            if date_filter:
                # Use the provided date filter
                formatted_date = date_filter.strftime('%Y-%m-%d %H:%M:%S')
                date_condition = f"WHERE created_at >= '{formatted_date}'"
            else:
                # Use the days parameter for relative filtering
                date_condition = f"WHERE created_at >= now() - INTERVAL {days} DAY"
            
            return client.execute_query(f"""
            SELECT 
                toDate(created_at) as day,
                count() as count
            FROM turn_events
            {date_condition}
            GROUP BY day
            ORDER BY day
            """)
        finally:
            client.close()

    @classmethod
    def get_response_type_distribution(cls) -> List[Tuple]:
        """Get distribution of response types"""
        client = cls._get_client()
        try:
            return client.execute_query("""
            SELECT 
                response_type,
                count() as count
            FROM turn_events
            GROUP BY response_type
            ORDER BY count DESC
            """)
        finally:
            client.close()

    @classmethod
    def get_citations_per_prompt_distribution(cls) -> List[Tuple]:
        """Get distribution of citations per prompt"""
        client = cls._get_client()
        try:
            return client.execute_query("""
            SELECT 
                CASE 
                    WHEN citation_count = 0 THEN '0 Citations'
                    WHEN citation_count = 1 THEN '1 Citation'
                    WHEN citation_count = 2 THEN '2 Citations'
                    WHEN citation_count = 3 THEN '3 Citations'
                    WHEN citation_count >= 4 THEN '4+ Citations'
                END as citation_group,
                CASE 
                    WHEN citation_count = 0 THEN 1
                    WHEN citation_count = 1 THEN 2
                    WHEN citation_count = 2 THEN 3
                    WHEN citation_count = 3 THEN 4
                    WHEN citation_count >= 4 THEN 5
                END as sort_order,
                count() as count
            FROM (
                SELECT 
                    te.thread_id,
                    te.turn_index,
                    count(ce.thread_id) as citation_count
                FROM turn_events te
                LEFT JOIN citation_events ce ON te.thread_id = ce.thread_id AND te.turn_index = ce.turn_id
                GROUP BY te.thread_id, te.turn_index
            ) as citation_counts
            GROUP BY citation_group, sort_order
            ORDER BY sort_order
            """)
        finally:
            client.close()

    @classmethod
    def get_length_distribution(cls) -> List[Tuple]:
        """Get distribution of response lengths in appropriate classes"""
        client = cls._get_client()
        try:
            # First get min and max to determine appropriate classes
            min_max_result = client.execute_query("""
            SELECT min(response_length), max(response_length)
            FROM turn_events
            WHERE response_length > 0
            """)
            
            if not min_max_result or not min_max_result[0]:
                return []
                
            min_length, max_length = min_max_result[0]
            
            # Create appropriate length classes based on the range
            if max_length <= 1000:
                # Small range, use 200-char intervals
                return client.execute_query("""
                SELECT 
                    CASE 
                        WHEN response_length = 0 THEN 'No Response'
                        WHEN response_length <= 200 THEN 'Very Short (≤200)'
                        WHEN response_length <= 400 THEN 'Short (201-400)'
                        WHEN response_length <= 600 THEN 'Medium (401-600)'
                        WHEN response_length <= 800 THEN 'Long (601-800)'
                        ELSE 'Very Long (800+)'
                    END as length_group,
                    CASE 
                        WHEN response_length = 0 THEN 1
                        WHEN response_length <= 200 THEN 2
                        WHEN response_length <= 400 THEN 3
                        WHEN response_length <= 600 THEN 4
                        WHEN response_length <= 800 THEN 5
                        ELSE 6
                    END as sort_order,
                    count() as count
                FROM turn_events
                GROUP BY length_group, sort_order
                ORDER BY sort_order
                """)
            else:
                # Larger range, use percentage-based classes
                return client.execute_query(f"""
                SELECT 
                    CASE 
                        WHEN response_length = 0 THEN 'No Response'
                        WHEN response_length <= {max_length * 0.2:.0f} THEN 'Very Short (≤{max_length * 0.2:.0f})'
                        WHEN response_length <= {max_length * 0.4:.0f} THEN 'Short ({max_length * 0.2:.0f}-{max_length * 0.4:.0f})'
                        WHEN response_length <= {max_length * 0.6:.0f} THEN 'Medium ({max_length * 0.4:.0f}-{max_length * 0.6:.0f})'
                        WHEN response_length <= {max_length * 0.8:.0f} THEN 'Long ({max_length * 0.6:.0f}-{max_length * 0.8:.0f})'
                        ELSE 'Very Long ({max_length * 0.8:.0f}+)'
                    END as length_group,
                    CASE 
                        WHEN response_length = 0 THEN 1
                        WHEN response_length <= {max_length * 0.2:.0f} THEN 2
                        WHEN response_length <= {max_length * 0.4:.0f} THEN 3
                        WHEN response_length <= {max_length * 0.6:.0f} THEN 4
                        WHEN response_length <= {max_length * 0.8:.0f} THEN 5
                        ELSE 6
                    END as sort_order,
                    count() as count
                FROM turn_events
                GROUP BY length_group, sort_order
                ORDER BY sort_order
                """)
        finally:
            client.close()

    @classmethod
    def get_sections_per_prompt_distribution(cls) -> List[Tuple]:
        """Get distribution of sections (paragraphs) per prompt"""
        client = cls._get_client()
        try:
            return client.execute_query("""
            SELECT 
                CASE 
                    WHEN response_num_sections = 0 THEN '0 Sections'
                    WHEN response_num_sections = 1 THEN '1 Section'
                    WHEN response_num_sections = 2 THEN '2 Sections'
                    WHEN response_num_sections = 3 THEN '3 Sections'
                    WHEN response_num_sections >= 4 THEN '4+ Sections'
                END as sections_group,
                CASE 
                    WHEN response_num_sections = 0 THEN 1
                    WHEN response_num_sections = 1 THEN 2
                    WHEN response_num_sections = 2 THEN 3
                    WHEN response_num_sections = 3 THEN 4
                    WHEN response_num_sections >= 4 THEN 5
                END as sort_order,
                count() as count
            FROM turn_events
            GROUP BY sections_group, sort_order
            ORDER BY sort_order
            """)
        finally:
            client.close()

    @classmethod
    def get_turns_per_thread_distribution(cls) -> List[Tuple]:
        """Get distribution of turns per thread"""
        client = cls._get_client()
        try:
            return client.execute_query("""
            SELECT 
                CASE 
                    WHEN turn_count = 1 THEN '1 Turn'
                    WHEN turn_count = 2 THEN '2 Turns'
                    WHEN turn_count = 3 THEN '3 Turns'
                    WHEN turn_count = 4 THEN '4 Turns'
                    WHEN turn_count >= 5 THEN '5+ Turns'
                END as turns_group,
                CASE 
                    WHEN turn_count = 1 THEN 1
                    WHEN turn_count = 2 THEN 2
                    WHEN turn_count = 3 THEN 3
                    WHEN turn_count = 4 THEN 4
                    WHEN turn_count >= 5 THEN 5
                END as sort_order,
                count() as count
            FROM (
                SELECT 
                    thread_id,
                    count() as turn_count
                FROM turn_events
                GROUP BY thread_id
            ) as thread_counts
            GROUP BY turns_group, sort_order
            ORDER BY sort_order
            """)
        finally:
            client.close() 