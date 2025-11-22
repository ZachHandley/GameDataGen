# Flet Components Guide

Learn how to build UI components for the GameDataGen desktop application.

## Table of Contents

- [Layout Components](#layout-components)
- [Input Components](#input-components)
- [Display Components](#display-components)
- [Custom Components](#custom-components)
- [Styling](#styling)
- [Best Practices](#best-practices)

## Layout Components

### Column

Vertical layout of controls:

```python
ft.Column([
    ft.Text("Header"),
    ft.Button("Action"),
    ft.Text("Footer"),
],
    spacing=10,
    scroll=ft.ScrollMode.AUTO,
    expand=True,
)
```

**Properties:**
- `spacing`: Vertical space between items
- `scroll`: Enable scrolling (AUTO, ALWAYS, HIDDEN)
- `expand`: Fill available space
- `horizontal_alignment`: LEFT, CENTER, RIGHT
- `vertical_alignment`: START, CENTER, END

### Row

Horizontal layout of controls:

```python
ft.Row([
    ft.Icon(ft.icons.HOME),
    ft.Text("Home"),
    ft.TextButton("Go"),
],
    spacing=15,
    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
)
```

**Properties:**
- `spacing`: Horizontal space between items
- `alignment`: SPACE_BETWEEN, SPACE_AROUND, CENTER, START, END
- `vertical_alignment`: TOP, CENTER, BOTTOM

### Container

Wrapper with padding, borders, and background:

```python
ft.Container(
    content=ft.Text("Contained"),
    padding=20,
    bgcolor=ft.colors.BLUE_100,
    border_radius=10,
    border=ft.border.all(2, ft.colors.BLUE),
    width=300,
    height=200,
)
```

**Properties:**
- `padding`: Inner spacing (number or `ft.padding.all(10)`)
- `margin`: Outer spacing
- `bgcolor`: Background color
- `border`: Border styling
- `border_radius`: Rounded corners
- `width`, `height`: Fixed dimensions
- `expand`: Fill available space

## Input Components

### TextField

Single-line text input:

```python
ft.TextField(
    label="Name",
    hint_text="Enter your name",
    value="",
    keyboard_type=ft.KeyboardType.TEXT,
    on_change=lambda e: print(e.control.value),
    width=300,
)
```

**Properties:**
- `label`: Floating label text
- `hint_text`: Placeholder text
- `value`: Current value
- `password`: Hide input (boolean)
- `multiline`: Allow multiple lines
- `keyboard_type`: TEXT, NUMBER, EMAIL, URL, PHONE
- `on_change`: Callback when value changes
- `on_submit`: Callback on Enter key

**Example: Validated Input**
```python
def validate_number(e):
    try:
        value = int(e.control.value)
        e.control.error_text = None
    except ValueError:
        e.control.error_text = "Must be a number"
    page.update()

ft.TextField(
    label="Age",
    on_change=validate_number,
)
```

### Dropdown

Selection from list:

```python
ft.Dropdown(
    label="Entity Type",
    value="npc",
    options=[
        ft.dropdown.Option("npc", "NPCs"),
        ft.dropdown.Option("quest", "Quests"),
        ft.dropdown.Option("item", "Items"),
    ],
    on_change=lambda e: print(e.control.value),
    width=200,
)
```

### Checkbox

Boolean selection:

```python
ft.Checkbox(
    label="Generate Images",
    value=False,
    on_change=lambda e: print(e.control.value),
)
```

### Slider

Numeric value selection:

```python
ft.Slider(
    min=0,
    max=1,
    divisions=10,
    label="{value}",
    value=0.5,
    on_change=lambda e: print(e.control.value),
    width=300,
)
```

### Button Variants

```python
# Elevated button (primary action)
ft.ElevatedButton(
    "Generate",
    icon=ft.icons.AUTO_AWESOME,
    on_click=handle_generate,
)

# Filled button (strong emphasis)
ft.FilledButton(
    "Save",
    icon=ft.icons.SAVE,
    on_click=handle_save,
)

# Outlined button (secondary action)
ft.OutlinedButton(
    "Cancel",
    on_click=handle_cancel,
)

# Text button (low emphasis)
ft.TextButton(
    "Skip",
    on_click=handle_skip,
)

# Icon button
ft.IconButton(
    icon=ft.icons.DELETE,
    on_click=handle_delete,
    tooltip="Delete",
)
```

## Display Components

### Text

Display text with styling:

```python
ft.Text(
    "Hello World",
    size=24,
    weight=ft.FontWeight.BOLD,
    color=ft.colors.BLUE,
    italic=True,
)
```

**Font Weights:**
- `NORMAL`, `BOLD`, `W_100` through `W_900`

### Icon

Material Design icons:

```python
ft.Icon(
    ft.icons.MIC,
    size=48,
    color=ft.colors.GREEN,
)
```

Browse icons: [Material Icons](https://fonts.google.com/icons)

### ProgressBar

Show progress or loading state:

```python
# Indeterminate (loading)
ft.ProgressBar(visible=True)

# Determinate (progress)
ft.ProgressBar(value=0.7, width=400)  # 70%
```

### Card

Elevated surface for grouping content:

```python
ft.Card(
    content=ft.Container(
        content=ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.icons.PERSON),
                title=ft.Text("John Doe"),
                subtitle=ft.Text("Level 50 Warrior"),
            ),
        ]),
        padding=10,
    ),
)
```

### ListTile

Structured list item:

```python
ft.ListTile(
    leading=ft.Icon(ft.icons.MIC),
    title=ft.Text("NPC Name"),
    subtitle=ft.Text("Voice: Assigned"),
    trailing=ft.IconButton(icon=ft.icons.PLAY_ARROW),
    on_click=handle_click,
)
```

### DataTable

Tabular data display:

```python
ft.DataTable(
    columns=[
        ft.DataColumn(ft.Text("Name")),
        ft.DataColumn(ft.Text("Level")),
        ft.DataColumn(ft.Text("Type")),
    ],
    rows=[
        ft.DataRow(cells=[
            ft.DataCell(ft.Text("Warrior")),
            ft.DataCell(ft.Text("50")),
            ft.DataCell(ft.Text("NPC")),
        ]),
    ],
)
```

### ListView

Scrollable list of items:

```python
list_view = ft.ListView(
    spacing=10,
    padding=20,
    expand=True,
)

# Add items
for item in data:
    list_view.controls.append(
        ft.Card(content=ft.Text(item.name))
    )
```

## Custom Components

### Stat Card Component

```python
def create_stat_card(
    title: str,
    value: str,
    icon: str,
    color: str = ft.colors.BLUE,
) -> ft.Card:
    """Create a statistics card"""
    return ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=40, color=color),
                ft.Container(height=10),
                ft.Text(
                    title,
                    size=14,
                    color=ft.colors.SECONDARY,
                ),
                ft.Text(
                    value,
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
            ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            padding=20,
            width=200,
        ),
    )

# Usage
card = create_stat_card(
    title="Total NPCs",
    value="127",
    icon=ft.icons.PERSON,
    color=ft.colors.GREEN,
)
```

### Loading Overlay

```python
def create_loading_overlay(message: str = "Loading...") -> ft.Container:
    """Create a loading overlay"""
    return ft.Container(
        content=ft.Column([
            ft.ProgressRing(),
            ft.Text(message, size=16),
        ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
        bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLACK),
        alignment=ft.alignment.center,
        expand=True,
    )
```

### Status Banner

```python
def create_status_banner(
    message: str,
    type: str = "info",  # info, success, warning, error
) -> ft.Container:
    """Create a status banner"""
    colors = {
        "info": ft.colors.BLUE,
        "success": ft.colors.GREEN,
        "warning": ft.colors.AMBER,
        "error": ft.colors.RED,
    }

    icons = {
        "info": ft.icons.INFO,
        "success": ft.icons.CHECK_CIRCLE,
        "warning": ft.icons.WARNING,
        "error": ft.icons.ERROR,
    }

    return ft.Container(
        content=ft.Row([
            ft.Icon(icons[type], color=colors[type]),
            ft.Text(message, expand=True),
        ]),
        bgcolor=ft.colors.with_opacity(0.2, colors[type]),
        border=ft.border.all(2, colors[type]),
        border_radius=5,
        padding=15,
    )
```

### Entity Card

```python
def create_entity_card(
    entity: dict,
    on_click: callable = None,
) -> ft.Card:
    """Create an entity card"""
    return ft.Card(
        content=ft.ListTile(
            leading=ft.Icon(ft.icons.DESCRIPTION),
            title=ft.Text(
                entity.get("name", "Unknown"),
                weight=ft.FontWeight.BOLD,
            ),
            subtitle=ft.Text(
                f"ID: {entity.get('id', '')}"
            ),
            trailing=ft.Icon(ft.icons.CHEVRON_RIGHT),
            on_click=on_click,
        ),
    )
```

## Styling

### Colors

```python
# Predefined colors
ft.colors.BLUE
ft.colors.RED_500
ft.colors.AMBER_ACCENT

# Custom colors
ft.colors.with_opacity(0.5, ft.colors.BLUE)

# Theme colors
ft.colors.PRIMARY
ft.colors.SECONDARY
ft.colors.SURFACE
ft.colors.ERROR
```

### Padding & Margin

```python
# All sides
ft.padding.all(10)
ft.margin.all(10)

# Symmetric
ft.padding.symmetric(horizontal=20, vertical=10)

# Individual
ft.padding.only(left=10, top=5, right=10, bottom=5)
```

### Borders

```python
# All sides
ft.border.all(2, ft.colors.BLUE)

# Individual sides
ft.border.only(
    left=ft.BorderSide(2, ft.colors.BLUE),
    top=ft.BorderSide(1, ft.colors.RED),
)
```

### Font Styling

```python
ft.Text(
    "Styled Text",
    size=20,                          # Font size
    weight=ft.FontWeight.BOLD,        # Font weight
    color=ft.colors.BLUE,             # Text color
    italic=True,                      # Italic
    font_family="Courier New",        # Font family
)
```

## Best Practices

### 1. Component Composition

Break complex UIs into smaller components:

```python
# ✅ Good - reusable components
def build_header() -> ft.Container:
    return ft.Container(content=ft.Text("Header"))

def build_content() -> ft.Column:
    return ft.Column([...])

page.add(
    ft.Column([
        build_header(),
        build_content(),
    ])
)

# ❌ Bad - monolithic UI
page.add(
    ft.Column([
        ft.Container(content=ft.Text("Header")),
        ft.Column([...]),  # Everything inline
    ])
)
```

### 2. Responsive Layouts

Use `expand` for flexible sizing:

```python
ft.Row([
    ft.Container(content=ft.Text("Sidebar"), width=200),
    ft.Container(content=ft.Text("Content"), expand=True),
])
```

### 3. Consistent Spacing

Define spacing constants:

```python
SPACING_SM = 5
SPACING_MD = 10
SPACING_LG = 20

ft.Column([...], spacing=SPACING_MD)
```

### 4. Color Theming

Use theme colors for consistency:

```python
# ✅ Good - theme colors
ft.Text("Error", color=ft.colors.ERROR)

# ❌ Bad - hardcoded colors
ft.Text("Error", color="#FF0000")
```

### 5. Accessibility

Add tooltips and labels:

```python
ft.IconButton(
    icon=ft.icons.DELETE,
    tooltip="Delete item",
    on_click=handle_delete,
)
```

## Interactive Examples

### Expandable Section

```python
class ExpandableSection:
    def __init__(self, title: str, content: ft.Control):
        self.title = title
        self.content = content
        self.expanded = False

    def build(self) -> ft.Column:
        header = ft.ListTile(
            leading=ft.Icon(
                ft.icons.EXPAND_MORE if self.expanded
                else ft.icons.CHEVRON_RIGHT
            ),
            title=ft.Text(self.title),
            on_click=self.toggle,
        )

        return ft.Column([
            header,
            self.content if self.expanded else ft.Container(height=0),
        ])

    async def toggle(self, e):
        self.expanded = not self.expanded
        await e.page.update_async()
```

### Confirmation Dialog

```python
async def show_confirm_dialog(
    page: ft.Page,
    title: str,
    message: str,
    on_confirm: callable,
) -> None:
    """Show confirmation dialog"""
    async def close_dialog():
        page.dialog.open = False
        await page.update_async()

    async def handle_confirm():
        await close_dialog()
        await on_confirm()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(message),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: close_dialog()),
            ft.FilledButton("Confirm", on_click=lambda e: handle_confirm()),
        ],
    )

    page.dialog = dialog
    dialog.open = True
    await page.update_async()
```

## Resources

- [Flet Controls Reference](https://flet.dev/docs/controls/)
- [Material Design Guidelines](https://m3.material.io/)
- [Flet Gallery](https://flet.dev/gallery/)
- [Component Examples](https://github.com/flet-dev/examples)

## Next Steps

- Review [Async Usage Guide](./async-usage.md) for async patterns
- Check [Desktop App Docs](./README.md) for architecture
- Explore [Flet Examples](https://github.com/flet-dev/examples)
