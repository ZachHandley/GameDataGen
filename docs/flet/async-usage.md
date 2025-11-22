# Async Usage Guide for Flet

Flet supports Python's `async`/`await` patterns, enabling concurrent operations without blocking the UI.

## Why Async in Flet?

### Benefits
- **Non-blocking UI**: Keep the interface responsive during I/O operations
- **Concurrent Operations**: Run multiple tasks simultaneously
- **Web Deployment**: Required for Pyodide (WebAssembly) targets
- **Modern Python**: Leverage `asyncio` ecosystem

### When to Use Async
- ✅ API calls (OpenAI, ElevenLabs, HTTP requests)
- ✅ File I/O operations
- ✅ Database queries
- ✅ Long-running computations
- ✅ Background tasks

### When NOT to Use Async
- ❌ Simple UI updates
- ❌ Synchronous calculations
- ❌ Event handlers that don't need I/O

## Basic Patterns

### Async Main Function

```python
import flet as ft

async def main(page: ft.Page):
    page.title = "Async App"

    # Async operations
    await asyncio.sleep(1)

    # UI updates
    page.add(ft.Text("Loaded!"))
    await page.update_async()

ft.app(target=main)
```

### Async Event Handlers

```python
async def on_button_click(e: ft.ControlEvent):
    # Show loading state
    e.control.disabled = True
    await e.page.update_async()

    # Do async work
    result = await fetch_data_from_api()

    # Update UI
    e.page.add(ft.Text(result))
    e.control.disabled = False
    await e.page.update_async()

button = ft.ElevatedButton("Load Data", on_click=on_button_click)
```

## GameDataGen Examples

### Content Generation

```python
async def generate_content(self) -> None:
    """Generate game content asynchronously"""
    try:
        # Show progress
        self.progress_bar.visible = True
        self.status_text.value = "Generating..."
        await self.page.update_async()

        # Run async generation
        results = await self.gen.generate(
            entity_type=self.entity_type,
            count=self.count,
            min_level=self.level_min,
            max_level=self.level_max,
        )

        # Update UI with results
        for result in results:
            card = ft.Card(content=ft.Text(result["name"]))
            self.results_list.controls.append(card)

        # Show success
        self.status_text.value = f"✓ Generated {len(results)} entities"
        self.progress_bar.visible = False
        await self.page.update_async()

    except Exception as error:
        # Handle errors
        self.status_text.value = f"Error: {str(error)}"
        self.status_text.color = ft.colors.ERROR
        await self.page.update_async()
```

### Voice Generation

```python
async def generate_voice(self, npc: dict) -> None:
    """Generate voice for NPC"""
    from gamedatagen.utils.voice_gen import VoiceGenerator

    # Initialize voice generator
    voice_gen = VoiceGenerator(api_key=self.config.elevenlabs_api_key)

    # Show status
    self.status_text.value = f"Generating voice for {npc['name']}..."
    await self.page.update_async()

    try:
        # Generate asynchronously
        result = await voice_gen.generate_and_save(
            entity_type="npc",
            entity_data=npc,
            output_dir=self.config.audio_dir / "npc",
            voice_id=npc["voice_id"],
        )

        # Update entity
        await self.gen.edit(
            entity_type="npc",
            entity_id=npc["id"],
            updates={"voice_metadata": result},
        )

        # Show success
        self.status_text.value = "✓ Voice generated successfully"
        self.status_text.color = ft.colors.GREEN
        await self.page.update_async()

    except Exception as error:
        self.status_text.value = f"Error: {error}"
        self.status_text.color = ft.colors.ERROR
        await self.page.update_async()
```

## Background Tasks

Use `page.run_task_async()` for long-running operations:

```python
async def on_generate_click(self, e: ft.ControlEvent) -> None:
    """Handle generate button click"""
    # Show loading UI
    self.progress_bar.visible = True
    await self.page.update_async()

    # Run in background
    await self.page.run_task_async(self.generate_content)

async def generate_content(self) -> None:
    """Background generation task"""
    # This runs asynchronously without blocking UI
    results = await self.gen.generate(...)

    # Update UI when done
    self.results_list.controls.extend(create_cards(results))
    await self.page.update_async()
```

## Common Patterns

### Loading States

```python
class DataLoader:
    def __init__(self, page: ft.Page):
        self.page = page
        self.loading = False
        self.progress = ft.ProgressBar(visible=False)

    async def with_loading(self, coro):
        """Execute coroutine with loading indicator"""
        try:
            self.loading = True
            self.progress.visible = True
            await self.page.update_async()

            result = await coro

            return result
        finally:
            self.loading = False
            self.progress.visible = False
            await self.page.update_async()

# Usage
loader = DataLoader(page)
results = await loader.with_loading(generate_npcs())
```

### Error Handling

```python
async def safe_api_call(self, operation: str, coro) -> None:
    """Execute API call with error handling"""
    try:
        self.status_text.value = f"{operation}..."
        self.status_text.color = ft.colors.SECONDARY
        await self.page.update_async()

        result = await coro

        self.status_text.value = f"✓ {operation} complete"
        self.status_text.color = ft.colors.GREEN
        await self.page.update_async()

        return result

    except Exception as error:
        self.status_text.value = f"Error during {operation}: {error}"
        self.status_text.color = ft.colors.ERROR
        await self.page.update_async()
        raise
```

### Batch Operations

```python
async def batch_generate(self, npcs: list) -> None:
    """Generate voices for multiple NPCs"""
    total = len(npcs)

    for i, npc in enumerate(npcs):
        # Update progress
        self.status_text.value = f"Processing {i+1}/{total}..."
        await self.page.update_async()

        # Process item
        await self.generate_voice(npc)

        # Small delay to keep UI responsive
        await asyncio.sleep(0.1)

    self.status_text.value = f"✓ Completed {total} NPCs"
    await self.page.update_async()
```

## Best Practices

### 1. Always Use `await page.update_async()`

```python
# ✅ Good
async def update_text(page, text):
    page.add(ft.Text(text))
    await page.update_async()

# ❌ Bad - UI won't update
async def update_text(page, text):
    page.add(ft.Text(text))
    # Missing await page.update_async()
```

### 2. Use `asyncio.sleep()` Not `time.sleep()`

```python
# ✅ Good - non-blocking
async def delayed_action():
    await asyncio.sleep(1)
    await do_something()

# ❌ Bad - blocks UI
async def delayed_action():
    time.sleep(1)  # This blocks!
    await do_something()
```

### 3. Handle Async in Event Handlers

```python
# ✅ Good - async handler
async def on_click(e: ft.ControlEvent):
    result = await fetch_data()
    await e.page.update_async()

button = ft.Button("Click", on_click=on_click)

# ❌ Bad - sync handler with async call
def on_click(e: ft.ControlEvent):
    result = await fetch_data()  # SyntaxError!
```

### 4. Use Background Tasks for Long Operations

```python
# ✅ Good - background task
async def on_button_click(e):
    await e.page.run_task_async(long_running_task)

async def long_running_task():
    # Runs in background
    await generate_100_npcs()

# ❌ Bad - blocks click handler
async def on_button_click(e):
    await generate_100_npcs()  # UI freezes
    await e.page.update_async()
```

### 5. Wrap Async Operations in Try/Except

```python
# ✅ Good
async def safe_operation():
    try:
        await risky_api_call()
    except Exception as error:
        show_error_dialog(error)

# ❌ Bad - unhandled errors crash app
async def unsafe_operation():
    await risky_api_call()  # May crash
```

## Advanced Patterns

### Concurrent Operations

```python
async def load_all_data(self) -> None:
    """Load multiple data sources concurrently"""
    # Run all in parallel
    npcs, quests, items = await asyncio.gather(
        self.gen.list_entities("npc"),
        self.gen.list_entities("quest"),
        self.gen.list_entities("item"),
    )

    # Update UI with all results
    self.populate_npcs(npcs)
    self.populate_quests(quests)
    self.populate_items(items)
    await self.page.update_async()
```

### Cancellable Tasks

```python
class CancellableOperation:
    def __init__(self):
        self.task = None

    async def start(self, page: ft.Page):
        """Start cancellable operation"""
        self.task = asyncio.create_task(self.long_operation())

        try:
            await self.task
        except asyncio.CancelledError:
            page.add(ft.Text("Operation cancelled"))
            await page.update_async()

    def cancel(self):
        """Cancel the operation"""
        if self.task:
            self.task.cancel()

    async def long_operation(self):
        for i in range(100):
            await asyncio.sleep(0.1)
            # Check if cancelled
            await asyncio.sleep(0)
```

### Streaming Updates

```python
async def stream_generation(self) -> None:
    """Stream generation results as they complete"""
    async for result in self.gen.generate_stream(count=10):
        # Add each result as it's generated
        card = create_card(result)
        self.results_list.controls.append(card)
        await self.page.update_async()
```

## Debugging Async Code

### Common Issues

**Issue**: `RuntimeWarning: coroutine 'x' was never awaited`
```python
# ❌ Bad
result = async_function()  # Missing await!

# ✅ Good
result = await async_function()
```

**Issue**: UI doesn't update
```python
# ❌ Bad
page.add(ft.Text("Hello"))
# Missing update

# ✅ Good
page.add(ft.Text("Hello"))
await page.update_async()
```

**Issue**: Async function runs but UI freezes
```python
# ❌ Bad - blocking sleep
async def slow():
    time.sleep(5)  # Blocks!

# ✅ Good - non-blocking
async def slow():
    await asyncio.sleep(5)
```

## Resources

- [Flet Async Apps Guide](https://flet.dev/docs/guides/python/async-apps)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Real Python Async Tutorial](https://realpython.com/async-io-python/)
- [Flet Examples Repository](https://github.com/flet-dev/examples)

## Next Steps

- Read [Components Guide](./components.md) for UI building
- Check [GameDataGen Desktop Docs](./README.md) for app architecture
- Explore Flet's [Controls Reference](https://flet.dev/docs/controls/)
