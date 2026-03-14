# Executing ComfyUI Workflows from JSON Files

This guide shows how to execute ComfyUI workflows loaded from JSON files.

## Methods

### Method 1: Using `execute_workflow_from_file()` (Recommended)

This is the simplest way to load and execute a workflow:

```python
from app.services.image_generation_service import ImageGenerationService

service = ImageGenerationService()

# Execute workflow as-is
image_path = service.execute_workflow_from_file(
    workflow_path="workflows/my_workflow.json",
    output_path="output.png"  # Optional
)

# Execute with prompt overrides
image_path = service.execute_workflow_from_file(
    workflow_path="workflows/my_workflow.json",
    prompt_overrides={
        "2:text": "A professional product showcase",  # Override node 2's text input
        "3:text": "blurry, low quality",  # Override node 3's text input
    }
)
```

### Method 2: Load then Execute Separately

```python
from app.services.image_generation_service import ImageGenerationService

service = ImageGenerationService()

# Load workflow
workflow = service.load_workflow_from_file("workflows/my_workflow.json")

if workflow:
    # Optionally modify the workflow
    workflow["2"]["inputs"]["text"] = "New prompt"
    
    # Execute
    image_path = service._execute_workflow(workflow, output_path="output.png")
```

### Method 3: Using `generate_hero_image()` with Workflow File

```python
from app.services.image_generation_service import ImageGenerationService

service = ImageGenerationService()

# Pass workflow file path as workflow_override
image_path = service.generate_hero_image(
    prompt="A professional product showcase",
    style="modern",
    workflow_override="workflows/my_workflow.json"  # File path as string
)
```

## Command Line Usage

### Execute a workflow file:

```bash
cd /Users/a0c1fjt/work/marketing-agent/backend
source .venv/bin/activate
python scripts/execute_workflow.py workflows/my_workflow.json
```

### With custom output path:

```bash
python scripts/execute_workflow.py workflows/my_workflow.json output.png
```

## Workflow JSON Formats Supported

The service supports multiple ComfyUI workflow JSON formats:

### Format 1: Direct Workflow (Most Common)
```json
{
  "1": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "model.safetensors"
    }
  },
  "2": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "a beautiful landscape",
      "clip": ["1", 1]
    }
  }
}
```

### Format 2: Wrapped Format
```json
{
  "workflow": {
    "1": {
      "class_type": "CheckpointLoaderSimple",
      "inputs": {
        "ckpt_name": "model.safetensors"
      }
    }
  },
  "extra": {
    "some_metadata": "value"
  }
}
```

### Format 3: Nodes Array Format
```json
{
  "nodes": [
    {
      "id": "1",
      "type": "CheckpointLoaderSimple",
      "properties": {
        "ckpt_name": "model.safetensors"
      }
    }
  ],
  "links": []
}
```

## Prompt Overrides

You can override specific node inputs when executing a workflow:

```python
prompt_overrides = {
    "2:text": "New positive prompt",      # Node 2, input "text"
    "3:text": "New negative prompt",      # Node 3, input "text"
    "5:seed": 12345,                      # Node 5, input "seed"
    "4:width": 1024,                      # Node 4, input "width"
}
```

The format is `"node_id:input_name"` -> `value`.

## Example: Complete Workflow

```python
from app.services.image_generation_service import ImageGenerationService

# Initialize service
service = ImageGenerationService()

if not service.comfyui_available:
    print("ComfyUI not available!")
    exit(1)

# Option 1: Execute workflow file directly
image_path = service.execute_workflow_from_file(
    workflow_path="workflows/hero_image.json",
    prompt_overrides={
        "2:text": "A modern product showcase for email marketing",
        "3:text": "blurry, low quality, watermark",
    },
    output_path="generated_hero.png"
)

if image_path:
    print(f"Image generated: {image_path}")
else:
    print("Generation failed")
```

## Troubleshooting

### Workflow Not Found
- Ensure the JSON file path is correct
- Check file permissions

### Invalid Workflow Structure
- Validate your JSON syntax
- Ensure all nodes have `class_type` and `inputs` fields
- Check that node references (like `["1", 0]`) point to valid nodes

### Model Not Found
- Check available models: `service.get_available_models()`
- Update the model name in your workflow JSON
- Or use prompt overrides to change the model node

### 400 Bad Request
- Check ComfyUI logs for detailed error messages
- Validate workflow structure matches ComfyUI's expected format
- Ensure all referenced nodes exist

## Getting Available Models

```python
service = ImageGenerationService()
models = service.get_available_models()
print(f"Available models: {models}")
```

## Validating a Workflow

```python
workflow = service.load_workflow_from_file("workflows/my_workflow.json")
is_valid, error = service.validate_workflow(workflow)
if not is_valid:
    print(f"Invalid workflow: {error}")
```










