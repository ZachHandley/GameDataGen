"""
Knowledge Graph for tracking entity relationships with rich metadata

Uses triplets: (subject, predicate, object, metadata)
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EntityReference(BaseModel):
    """Reference to an entity in the graph"""

    type: str  # Entity type (Quest, NPC, Item, etc.)
    id: str  # Entity ID


class RelationMetadata(BaseModel):
    """Rich metadata for relationships"""

    # Optional/conditional
    optional: Optional[bool] = None
    chance: Optional[float] = None  # Probability 0-1
    level_required: Optional[int] = None

    # Weighted relationships
    weight: Optional[float] = None
    priority: Optional[int] = None

    # Spatial data
    coordinates: Optional[Dict[str, float]] = None
    distance: Optional[float] = None

    # Temporal data
    schedule: Optional[str] = None  # Cron-like or time range
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    # Custom metadata
    custom: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Triplet(BaseModel):
    """Knowledge graph triplet"""

    subject: EntityReference
    predicate: str  # Relationship type
    object: EntityReference
    metadata: Optional[RelationMetadata] = None


class KnowledgeGraph:
    """Knowledge graph for entity relationships"""

    def __init__(self) -> None:
        self.triplets: List[Triplet] = []

        # Indexes for fast queries
        self._subject_index: Dict[str, List[Triplet]] = {}
        self._object_index: Dict[str, List[Triplet]] = {}
        self._predicate_index: Dict[str, List[Triplet]] = {}

    def add_triplet(self, triplet: Triplet) -> None:
        """Add a triplet to the graph"""
        self.triplets.append(triplet)

        # Update indexes
        subject_key = f"{triplet.subject.type}:{triplet.subject.id}"
        object_key = f"{triplet.object.type}:{triplet.object.id}"

        if subject_key not in self._subject_index:
            self._subject_index[subject_key] = []
        self._subject_index[subject_key].append(triplet)

        if object_key not in self._object_index:
            self._object_index[object_key] = []
        self._object_index[object_key].append(triplet)

        if triplet.predicate not in self._predicate_index:
            self._predicate_index[triplet.predicate] = []
        self._predicate_index[triplet.predicate].append(triplet)

    def find(
        self,
        subject: Optional[EntityReference] = None,
        predicate: Optional[str] = None,
        object: Optional[EntityReference] = None,
    ) -> List[Triplet]:
        """Find triplets matching criteria"""

        # Start with all triplets or indexed subset
        if subject:
            key = f"{subject.type}:{subject.id}"
            candidates = self._subject_index.get(key, [])
        elif object:
            key = f"{object.type}:{object.id}"
            candidates = self._object_index.get(key, [])
        elif predicate:
            candidates = self._predicate_index.get(predicate, [])
        else:
            candidates = self.triplets

        # Filter
        results = []
        for triplet in candidates:
            if subject and (
                triplet.subject.type != subject.type or triplet.subject.id != subject.id
            ):
                continue

            if predicate and triplet.predicate != predicate:
                continue

            if object and (
                triplet.object.type != object.type or triplet.object.id != object.id
            ):
                continue

            results.append(triplet)

        return results

    def get_related(
        self,
        entity: EntityReference,
        predicate: Optional[str] = None,
        direction: str = "outgoing",
    ) -> List[EntityReference]:
        """Get entities related to this entity"""

        if direction == "outgoing":
            triplets = self.find(subject=entity, predicate=predicate)
            return [t.object for t in triplets]
        elif direction == "incoming":
            triplets = self.find(object=entity, predicate=predicate)
            return [t.subject for t in triplets]
        else:  # both
            outgoing = self.find(subject=entity, predicate=predicate)
            incoming = self.find(object=entity, predicate=predicate)
            return [t.object for t in outgoing] + [t.subject for t in incoming]

    def get_relationship(
        self, subject: EntityReference, object: EntityReference
    ) -> Optional[Triplet]:
        """Get relationship between two entities"""

        triplets = self.find(subject=subject, object=object)
        return triplets[0] if triplets else None

    def remove_entity(self, entity: EntityReference) -> int:
        """Remove all triplets involving an entity"""

        subject_key = f"{entity.type}:{entity.id}"
        object_key = subject_key

        # Find all triplets
        to_remove = set()
        for triplet in self.triplets:
            if (
                triplet.subject.type == entity.type
                and triplet.subject.id == entity.id
            ) or (triplet.object.type == entity.type and triplet.object.id == entity.id):
                to_remove.add(id(triplet))

        # Remove from main list
        self.triplets = [t for t in self.triplets if id(t) not in to_remove]

        # Rebuild indexes
        self._rebuild_indexes()

        return len(to_remove)

    def _rebuild_indexes(self) -> None:
        """Rebuild all indexes"""
        self._subject_index = {}
        self._object_index = {}
        self._predicate_index = {}

        for triplet in self.triplets:
            subject_key = f"{triplet.subject.type}:{triplet.subject.id}"
            object_key = f"{triplet.object.type}:{triplet.object.id}"

            if subject_key not in self._subject_index:
                self._subject_index[subject_key] = []
            self._subject_index[subject_key].append(triplet)

            if object_key not in self._object_index:
                self._object_index[object_key] = []
            self._object_index[object_key].append(triplet)

            if triplet.predicate not in self._predicate_index:
                self._predicate_index[triplet.predicate] = []
            self._predicate_index[triplet.predicate].append(triplet)

    def stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""

        entity_types = set()
        predicates = set()
        entities = set()

        for triplet in self.triplets:
            entity_types.add(triplet.subject.type)
            entity_types.add(triplet.object.type)
            predicates.add(triplet.predicate)
            entities.add(f"{triplet.subject.type}:{triplet.subject.id}")
            entities.add(f"{triplet.object.type}:{triplet.object.id}")

        return {
            "triplets": len(self.triplets),
            "entities": len(entities),
            "entity_types": len(entity_types),
            "relationship_types": len(predicates),
            "predicates": list(predicates),
        }

    def export(self) -> List[Dict[str, Any]]:
        """Export knowledge graph to JSON"""
        return [t.model_dump() for t in self.triplets]

    def import_triplets(self, data: List[Dict[str, Any]]) -> None:
        """Import triplets from JSON"""
        for item in data:
            triplet = Triplet(**item)
            self.add_triplet(triplet)
