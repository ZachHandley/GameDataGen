"""
Schema Registry with dynamic Pydantic model creation from JSON schemas

Accepts user-provided JSON schemas and converts them to Pydantic models at runtime.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml
from pydantic import BaseModel, Field, create_model


class SchemaDefinition(BaseModel):
    """Schema definition metadata"""

    model_config = {"protected_namespaces": ()}  # Allow "schema" field

    name: str
    description: Optional[str] = None
    schema: Dict[str, Any]  # JSON Schema
    dependencies: List[str] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)


class SchemaRegistry:
    """Registry for user-provided schemas with dynamic Pydantic model creation"""

    def __init__(self) -> None:
        self.schemas: Dict[str, SchemaDefinition] = {}
        self.models: Dict[str, Type[BaseModel]] = {}

    def register_from_json_schema(
        self,
        name: str,
        json_schema: Dict[str, Any],
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
    ) -> Type[BaseModel]:
        """
        Register a schema from JSON Schema and create dynamic Pydantic model

        Args:
            name: Schema name
            json_schema: JSON Schema definition
            description: Schema description
            dependencies: List of dependent schema names

        Returns:
            Dynamically created Pydantic model
        """
        # Store schema definition
        schema_def = SchemaDefinition(
            name=name,
            description=description,
            schema=json_schema,
            dependencies=dependencies or [],
        )
        self.schemas[name] = schema_def

        # Convert JSON Schema to Pydantic model
        model = self._json_schema_to_pydantic(name, json_schema)
        self.models[name] = model

        return model

    def register_from_file(self, filepath: Path) -> Type[BaseModel]:
        """
        Register schema from YAML/JSON file

        File format:
            name: Quest
            description: A quest or mission
            schema:
              type: object
              properties:
                id: {type: string}
                name: {type: string}
            dependencies: []
        """
        with open(filepath) as f:
            if filepath.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        return self.register_from_json_schema(
            name=data["name"],
            json_schema=data["schema"],
            description=data.get("description"),
            dependencies=data.get("dependencies", []),
        )

    def get_model(self, name: str) -> Type[BaseModel]:
        """Get Pydantic model by name"""
        if name not in self.models:
            raise ValueError(f"Schema not registered: {name}")
        return self.models[name]

    def get_schema(self, name: str) -> SchemaDefinition:
        """Get schema definition by name"""
        if name not in self.schemas:
            raise ValueError(f"Schema not registered: {name}")
        return self.schemas[name]

    def validate(self, name: str, data: Dict[str, Any]) -> BaseModel:
        """Validate data against schema"""
        model = self.get_model(name)
        return model(**data)

    def list_schemas(self) -> List[str]:
        """List all registered schema names"""
        return list(self.schemas.keys())

    def _json_schema_to_pydantic(
        self, name: str, json_schema: Dict[str, Any]
    ) -> Type[BaseModel]:
        """
        Convert JSON Schema to Pydantic model dynamically

        Uses create_model to build Pydantic models at runtime from JSON Schema.
        """
        if json_schema.get("type") != "object":
            raise ValueError(f"Only object type schemas supported, got: {json_schema.get('type')}")

        properties = json_schema.get("properties", {})
        required = set(json_schema.get("required", []))

        # Build field definitions for create_model
        field_definitions: Dict[str, Any] = {}

        for field_name, field_schema in properties.items():
            field_type, default = self._get_field_type(field_schema, field_name in required)
            field_definitions[field_name] = (field_type, default)

        # Create dynamic Pydantic model
        return create_model(name, **field_definitions)

    def _get_field_type(
        self, field_schema: Dict[str, Any], is_required: bool
    ) -> tuple[Any, Any]:
        """
        Get Python type and default value from JSON Schema field

        Returns:
            (type_annotation, default_value)
        """
        field_type = field_schema.get("type")
        enum_values = field_schema.get("enum")

        # Handle enums
        if enum_values:
            # For enums, we'll just use str for now (could create Literal types)
            python_type = str
        # Handle types
        elif field_type == "string":
            python_type = str
        elif field_type == "integer":
            python_type = int
        elif field_type == "number":
            python_type = float
        elif field_type == "boolean":
            python_type = bool
        elif field_type == "array":
            # Get item type
            items_schema = field_schema.get("items", {})
            item_type = self._get_field_type(items_schema, False)[0]
            python_type = List[item_type]  # type: ignore
        elif field_type == "object":
            # Nested object - use Dict for now
            # Could recursively create nested models if needed
            python_type = Dict[str, Any]
        else:
            # Unknown type, use Any
            python_type = Any

        # Handle optional fields
        if not is_required:
            python_type = Optional[python_type]  # type: ignore
            default = None
        else:
            default = ...  # Required field (Ellipsis)

        return python_type, default

    def load_schemas_from_directory(self, directory: Path) -> int:
        """
        Load all schemas from a directory

        Args:
            directory: Directory containing schema files

        Returns:
            Number of schemas loaded
        """
        count = 0
        for filepath in directory.glob("*.yaml"):
            try:
                self.register_from_file(filepath)
                count += 1
            except Exception as e:
                print(f"Warning: Failed to load schema {filepath}: {e}")

        for filepath in directory.glob("*.yml"):
            try:
                self.register_from_file(filepath)
                count += 1
            except Exception as e:
                print(f"Warning: Failed to load schema {filepath}: {e}")

        for filepath in directory.glob("*.json"):
            try:
                self.register_from_file(filepath)
                count += 1
            except Exception as e:
                print(f"Warning: Failed to load schema {filepath}: {e}")

        return count

    def export_json_schema(self, name: str) -> Dict[str, Any]:
        """Export schema as JSON Schema"""
        return self.schemas[name].schema

    def export_pydantic_schema(self, name: str) -> Dict[str, Any]:
        """Export as Pydantic schema (JSON Schema from model)"""
        model = self.get_model(name)
        return model.model_json_schema()
