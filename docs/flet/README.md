# GameDataGen Desktop Application (Flet)

GameDataGen includes a modern desktop GUI built with [Flet](https://flet.dev), a Python framework for building Flutter-based applications.

## What is Flet?

Flet is a framework that enables developers to build real-time web, mobile, and desktop applications using **pure Python**. No frontend experience required!

### Key Benefits

- **Pure Python** - No JavaScript, HTML, or CSS needed
- **Flutter-Powered** - Professional UI with excellent performance
- **Cross-Platform** - Works on Windows, macOS, Linux, web, and mobile
- **Async/Await Support** - First-class async support for concurrent operations
- **Built-in Tools** - No complex tooling or SDKs required

## Launching the Desktop App

```bash
# Navigate to your GameDataGen project
cd my-rpg-game

# Launch the desktop interface
gamedatagen desktop
```

The application will:
1. Auto-detect your project configuration
2. Load your game content
3. Open a native desktop window

## Features

### 🎮 Content Generation
- Visual form for generating NPCs, quests, items, enemies
- Real-time progress indicators
- Results preview with entity cards
- Support for images and voices

### 🎙️ Voice Management
- List all NPCs with dialogue
- Assign ElevenLabs voices to NPCs
- Generate voices for individual NPCs or batch process
- Visual indicators for voice assignment status

### 📊 Project Statistics
- Entity counts and breakdown
- Knowledge graph statistics
- Storage usage metrics
- Visual charts and graphs

### ⚙️ Settings
- Configure API keys (OpenAI, ElevenLabs, Anthropic)
- Adjust generation parameters (model, temperature, max level)
- Fine-tune voice settings (stability, similarity boost)
- Save settings to project config

## Architecture

```
src/gamedatagen/desktop/
├── app.py                 # Main application entry point
├── views/                 # View components
│   ├── content_view.py   # Content generation UI
│   ├── voice_view.py     # Voice management UI
│   ├── stats_view.py     # Statistics dashboard
│   └── settings_view.py  # Settings panel
└── components/            # Reusable UI components
```

## Documentation

- **[Async Usage](./async-usage.md)** - Learn how to use Flet with async/await
- **[Components Guide](./components.md)** - Understand the UI component structure
- **[Flet Official Docs](https://flet.dev/docs/)** - Complete Flet documentation
- **[Flet Examples](https://github.com/flet-dev/examples)** - Example applications

## External Resources

### Official Flet Links
- 🌐 [Flet.dev Homepage](https://flet.dev)
- 📖 [Flet Documentation](https://flet.dev/docs/)
- 🐍 [Python Async Apps Guide](https://flet.dev/docs/guides/python/async-apps)
- 🎨 [Controls Reference](https://flet.dev/docs/controls/)
- 🚀 [Getting Started Tutorial](https://flet.dev/docs/getting-started/)
- 💻 [GitHub Repository](https://github.com/flet-dev/flet)
- 💬 [Discord Community](https://discord.gg/dzWXP8SHG8)

### Key Concepts

**Declarative UI**: Build interfaces by describing what you want, not how to build it
```python
ft.Column([
    ft.Text("Hello World"),
    ft.Button("Click Me"),
])
```

**Real-time Updates**: UI automatically updates when you change control properties
```python
text_control.value = "New value"
await page.update_async()
```

**Event Handling**: Connect callbacks to user interactions
```python
ft.Button("Click", on_click=handle_click)
```

**Async Support**: Use async/await for non-blocking operations
```python
async def main(page: ft.Page):
    await asyncio.sleep(1)
    await page.update_async()
```

## Development

### Running in Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run the desktop app
uv run gamedatagen desktop
```

### Adding New Views

1. Create a new view file in `src/gamedatagen/desktop/views/`
2. Implement the view class with a `build()` method
3. Add navigation in `app.py`
4. Register in `views/__init__.py`

Example:
```python
class MyCustomView:
    def __init__(self, page: ft.Page, config: ProjectConfig, gen: GameDataGen):
        self.page = page
        self.config = config
        self.gen = gen

    async def build(self) -> ft.Column:
        return ft.Column([
            ft.Text("My Custom View"),
            # ... more UI components
        ])
```

### Adding New Components

Create reusable components in `src/gamedatagen/desktop/components/`:

```python
def create_stat_card(title: str, value: str) -> ft.Card:
    return ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text(title),
                ft.Text(value, size=24, weight=ft.FontWeight.BOLD),
            ]),
            padding=20,
        )
    )
```

## Troubleshooting

### App Won't Launch

**Issue**: "No GameDataGen project found"
**Solution**: Run from a directory with a `.gamedatagen/config.yaml` file

**Issue**: Flet not installed
**Solution**: `uv sync` or `pip install flet>=0.23.0`

### API Keys Not Working

**Issue**: Voice generation fails
**Solution**: Configure ElevenLabs API key in Settings view or `.gamedatagen/config.yaml`

**Issue**: Content generation fails
**Solution**: Configure OpenAI/Anthropic API key in Settings

### Performance Issues

**Issue**: UI freezes during generation
**Solution**: The app uses `page.run_task_async()` for background tasks. Ensure long operations are async.

## Best Practices

1. **Use Async for I/O Operations**: Always use `async def` for API calls, file operations
2. **Update UI After Changes**: Call `await page.update_async()` after modifying controls
3. **Handle Errors Gracefully**: Wrap async operations in try/except blocks
4. **Keep UI Responsive**: Use background tasks for long-running operations
5. **Follow Flet Patterns**: Use containers, columns, rows for layout

## Examples

### Simple Dialog
```python
async def show_dialog(page: ft.Page, message: str):
    dialog = ft.AlertDialog(
        title=ft.Text("Info"),
        content=ft.Text(message),
        actions=[ft.TextButton("OK", on_click=lambda e: close_dialog())],
    )
    page.dialog = dialog
    dialog.open = True
    await page.update_async()
```

### Progress Indicator
```python
progress = ft.ProgressBar(visible=False)
progress.visible = True
await page.update_async()

# Do work...
await asyncio.sleep(2)

progress.visible = False
await page.update_async()
```

### Data List
```python
list_view = ft.ListView(spacing=10)
for item in data:
    list_view.controls.append(
        ft.Card(content=ft.ListTile(title=ft.Text(item.name)))
    )
await page.update_async()
```

## Next Steps

- Read [Async Usage Guide](./async-usage.md) for async patterns
- Explore [Components Guide](./components.md) for UI building blocks
- Check [Flet Docs](https://flet.dev/docs/) for complete reference
- Join [Flet Discord](https://discord.gg/dzWXP8SHG8) for community support
