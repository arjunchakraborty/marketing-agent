"""MCP-AGUI protocol adapter for UI interoperability."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MCPAGUIView(BaseModel):
    """MCP-AGUI view definition."""

    view_id: str
    view_type: str = Field(..., description="Type of view: dashboard, chart, table, etc.")
    title: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MCPAGUIAdapter:
    """Adapter for MCP-AGUI protocol UI embedding and interoperability."""

    def __init__(self) -> None:
        self.registered_views: Dict[str, MCPAGUIView] = {}

    def register_view(self, view: MCPAGUIView) -> None:
        """Register a view for MCP-AGUI exposure."""
        self.registered_views[view.view_id] = view

    def get_view(self, view_id: str) -> Optional[MCPAGUIView]:
        """Retrieve a registered view by ID."""
        return self.registered_views.get(view_id)

    def list_views(self, view_type: Optional[str] = None) -> List[MCPAGUIView]:
        """List all registered views, optionally filtered by type."""
        views = list(self.registered_views.values())
        if view_type:
            return [v for v in views if v.view_type == view_type]
        return views

    def expose_dashboard(self, dashboard_id: str, title: str, data: Dict[str, Any]) -> MCPAGUIView:
        """Expose a dashboard view via MCP-AGUI."""
        view = MCPAGUIView(
            view_id=dashboard_id,
            view_type="dashboard",
            title=title,
            data=data,
            metadata={"protocol": "mcp-agui", "version": "1.0"},
        )
        self.register_view(view)
        return view

