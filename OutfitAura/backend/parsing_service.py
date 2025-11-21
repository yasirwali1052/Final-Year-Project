import os
import sys
import uuid
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms
from collections import OrderedDict

# --- Locate the Self-Correction Human Parsing repo ---
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# Allow overriding via environment variable
custom_repo_path = os.getenv("PARSING_REPO_PATH")
candidate_paths = []
if custom_repo_path:
    candidate_paths.append(Path(custom_repo_path))

# Check backend directory then project root
# Check backend directory, project root, then grandparent (workspace root)
candidate_paths.extend(
    [
        BACKEND_DIR / "Self-Correction-Human-Parsing-master",
        PROJECT_ROOT / "Self-Correction-Human-Parsing-master",
        PROJECT_ROOT.parent / "Self-Correction-Human-Parsing-master",
    ]
)

PARSING_REPO = next((path for path in candidate_paths if path.exists()), None)

if PARSING_REPO:
    sys.path.append(str(PARSING_REPO))
else:
    raise FileNotFoundError(
        "Self-Correction-Human-Parsing-master directory not found. "
        "Set PARSING_REPO_PATH or place the folder in backend/ or project root."
    )

from networks import init_model  # type: ignore  # noqa: E402


class ParsingService:
    def __init__(
        self,
        weights_path: Optional[Path] = None,
        device: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ) -> None:
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.weights_path = weights_path or (PARSING_REPO / "models" / "exp-schp-201908261155-lip.pth")
        if not self.weights_path.exists():
            raise FileNotFoundError(f"Parsing weights not found at {self.weights_path}")

        self.output_dir = output_dir or (BACKEND_DIR / "static" / "parsing")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.num_classes = 20
        self.input_size = (768, 768)  # Height, Width
        self.palette = self._build_palette(self.num_classes)
        self.transform = transforms.Compose(
            [
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.406, 0.456, 0.485], std=[0.225, 0.224, 0.229]),
            ]
        )

        self.model = self._load_model().to(self.device)
        self.model.eval()

    def _load_model(self):
        model = init_model("resnet101", num_classes=self.num_classes, pretrained=None)
        state_dict = torch.load(self.weights_path, map_location=self.device)
        if "state_dict" in state_dict:
            state_dict = state_dict["state_dict"]

        cleaned_state = OrderedDict()
        for key, value in state_dict.items():
            new_key = key[7:] if key.startswith("module.") else key
            cleaned_state[new_key] = value

        model.load_state_dict(cleaned_state, strict=False)
        return model

    def _build_palette(self, num_cls: int) -> list[int]:
        palette = [0] * (num_cls * 3)
        for j in range(num_cls):
            lab = j
            i = 0
            while lab:
                palette[j * 3 + 0] |= (((lab >> 0) & 1) << (7 - i))
                palette[j * 3 + 1] |= (((lab >> 1) & 1) << (7 - i))
                palette[j * 3 + 2] |= (((lab >> 2) & 1) << (7 - i))
                i += 1
                lab >>= 3
        return palette

    def generate_parsing(self, image_path: Path) -> Path:
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        image = Image.open(image_path).convert("RGB")
        orig_w, orig_h = image.size
        resized = image.resize((self.input_size[1], self.input_size[0]), Image.BILINEAR)
        tensor = self.transform(resized).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(tensor)
            if isinstance(outputs, (list, tuple)):
                parsing_logits = outputs[0][-1][0].unsqueeze(0)
            else:
                parsing_logits = outputs

            if isinstance(parsing_logits, list):
                parsing_logits = parsing_logits[-1]

            parsing_logits = F.interpolate(
                parsing_logits,
                size=(orig_h, orig_w),
                mode="bilinear",
                align_corners=True,
            )

            parsing = parsing_logits.squeeze(0).cpu().numpy().argmax(0)

        output_path = self.output_dir / f"{uuid.uuid4().hex}_parsing.png"
        parsing_img = Image.fromarray(parsing.astype(np.uint8), mode="P")
        parsing_img.putpalette(self.palette)
        parsing_img.save(output_path)

        return output_path


# Create a singleton instance that can be reused across FastAPI requests
parsing_service = ParsingService()

