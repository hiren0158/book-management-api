import base64
import json
from typing import Generic, TypeVar, Type, Optional, Any, Callable
from datetime import datetime
from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, and_, extract

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, data: dict) -> T:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, id: int) -> Optional[T]:
        statement = select(self.model).where(self.model.id == id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(
        self,
        limit: int = 10,
        cursor: Optional[str] = None,
        filters: Optional[dict] = None,
        search_fields: Optional[list[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "desc",  # "asc" or "desc"
        custom_filters: Optional[list[Callable]] = None,
    ) -> tuple[list[T], Optional[str]]:
        """
        List items with pagination, filtering, and search.
        
        Args:
            limit: Maximum number of items to return
            cursor: Cursor for pagination
            filters: Dict of exact match filters (field: value)
            search_fields: Fields to search in for search_query
            search_query: Text to search for across search_fields
            sort_order: "asc" or "desc"
            custom_filters: List of callable functions that take a statement and return a modified statement
        """
        statement = select(self.model)

        if cursor:
            cursor_data = self._decode_cursor(cursor)
            created_at = datetime.fromisoformat(cursor_data["created_at"])
            cursor_id = cursor_data["id"]
            
            if sort_order == "asc":
                statement = statement.where(
                    or_(
                        self.model.created_at > created_at,
                        and_(
                            self.model.created_at == created_at,
                            self.model.id > cursor_id
                        )
                    )
                )
            else:  # desc
                statement = statement.where(
                    or_(
                        self.model.created_at < created_at,
                        and_(
                            self.model.created_at == created_at,
                            self.model.id < cursor_id
                        )
                    )
                )

        # Apply exact match filters
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    statement = statement.where(getattr(self.model, field) == value)

        # Apply custom filters (for complex queries like date/year extraction)
        if custom_filters:
            for filter_func in custom_filters:
                statement = filter_func(statement)

        # Apply text search across multiple fields with smart word matching
        if search_query and search_fields:
            import re
            keywords = search_query.split()
            search_conditions = []
            
            # Common abbreviations mapping
            abbreviations = {
                'db': 'database',
                'ai': 'artificial intelligence',
                'ml': 'machine learning',
                'dl': 'deep learning',
                'nlp': 'natural language processing',
                'api': 'application programming interface',
                'sql': 'structured query language',
                'ui': 'user interface',
                'ux': 'user experience',
                'js': 'javascript',
                'py': 'python',
                'cs': 'computer science',
                'it': 'information technology',
                'iot': 'internet of things',
                'ci': 'continuous integration',
                'cd': 'continuous deployment',
            }
            
            # Synonym expansion for better semantic matching
            synonyms = {
                'underwater': ['deep-sea', 'ocean', 'submarine', 'aquatic'],
                'deep-sea': ['underwater', 'ocean', 'submarine'],
                'ocean': ['underwater', 'deep-sea', 'sea', 'marine'],
                'space': ['galaxy', 'cosmic', 'universe', 'stellar'],
                'galaxy': ['space', 'cosmic', 'universe', 'stellar'],
                'ancient': ['old', 'historical', 'antiquity'],
                'old': ['ancient', 'historical', 'vintage'],
                'future': ['futuristic', 'tomorrow', 'advanced'],
                'futuristic': ['future', 'tomorrow', 'advanced'],
                'scary': ['horror', 'frightening', 'terrifying'],
                'horror': ['scary', 'frightening', 'terrifying'],
            }
            
            for keyword in keywords:
                keyword_conditions = []
                keyword_lower = keyword.lower()
                
                # Generate variations of the keyword to match
                variations = [keyword_lower]
                
                # Check if keyword has synonyms
                if keyword_lower in synonyms:
                    variations.extend(synonyms[keyword_lower])
                
                # Check if keyword is a known abbreviation
                if keyword_lower in abbreviations:
                    full_form = abbreviations[keyword_lower]
                    # Add the full form and its variations
                    variations.append(full_form)
                    # Also add plural
                    if not full_form.endswith('s'):
                        variations.append(full_form + 's')
                
                # Add plural form if doesn't end with 's'
                if not keyword_lower.endswith('s'):
                    variations.append(keyword_lower + 's')
                
                # Remove 's' if ends with 's' (handle plurals)
                if keyword_lower.endswith('s') and len(keyword_lower) > 3:
                    variations.append(keyword_lower[:-1])
                
                # Handle -ing forms (coding -> code)
                if keyword_lower.endswith('ing') and len(keyword_lower) > 4:
                    base = keyword_lower[:-3]
                    variations.append(base)  # coding -> cod
                    variations.append(base + 'e')  # coding -> code
                
                # Handle -ed forms (coded -> code)
                if keyword_lower.endswith('ed') and len(keyword_lower) > 3:
                    base = keyword_lower[:-2]
                    variations.append(base)  # coded -> cod
                    variations.append(base + 'e')  # coded -> code
                
                # Remove duplicates
                variations = list(set(variations))
                
                # Search for any variation in any field
                for variation in variations:
                    for field in search_fields:
                        if hasattr(self.model, field):
                            keyword_conditions.append(
                                getattr(self.model, field).ilike(f"%{variation}%")
                            )
                
                if keyword_conditions:
                    # Any variation of this keyword must match (OR)
                    search_conditions.append(or_(*keyword_conditions))
            
            if search_conditions:
                # All keywords must match (AND logic)
                statement = statement.where(and_(*search_conditions))

        if sort_order == "asc":
            statement = statement.order_by(
                self.model.created_at.asc(),
                self.model.id.asc()
            )
        else:
            statement = statement.order_by(
                self.model.created_at.desc(),
                self.model.id.desc()
            )
            
        statement = statement.limit(limit + 1)

        result = await self.session.execute(statement)
        items = list(result.scalars().all())

        next_cursor = None
        if len(items) > limit:
            items = items[:limit]
            last_item = items[-1]
            next_cursor = self._encode_cursor(last_item.created_at, last_item.id)

        return items, next_cursor

    async def update(self, id: int, data: dict) -> Optional[T]:
        instance = await self.get_by_id(id)
        if not instance:
            return None

        for field, value in data.items():
            if value is not None and hasattr(instance, field):
                setattr(instance, field, value)

        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        instance = await self.get_by_id(id)
        if not instance:
            return False

        await self.session.delete(instance)
        await self.session.commit()
        return True

    async def count(self, filters: Optional[dict] = None) -> int:
        statement = select(func.count()).select_from(self.model)

        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    statement = statement.where(getattr(self.model, field) == value)

        result = await self.session.execute(statement)
        return result.scalar_one()

    def _encode_cursor(self, created_at: datetime, id: int) -> str:
        cursor_data = {
            "created_at": created_at.isoformat(),
            "id": id
        }
        json_str = json.dumps(cursor_data)
        return base64.b64encode(json_str.encode()).decode()

    def _decode_cursor(self, cursor: str) -> dict:
        try:
            json_str = base64.b64decode(cursor.encode()).decode()
            return json.loads(json_str)
        except Exception:
            raise ValueError("Invalid cursor format")
