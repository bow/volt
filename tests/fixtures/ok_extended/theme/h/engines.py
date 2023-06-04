from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import yaml
from volt import Engine, CopyTarget, TemplateTarget
from volt.engines import MarkdownEngine


@dataclass
class ImageSource:
    caption: str
    path: Path


class GalleryEngine(Engine):
    def create_targets(self) -> Sequence[TemplateTarget | CopyTarget]:
        targets: list[TemplateTarget | CopyTarget] = []

        template = self.theme.load_template_file("image.html.j2")

        for image in self.get_sources():
            copy_target = CopyTarget(
                src=image.path,
                url_parts=("assets", "imgs", image.path.name),
            )
            template_target = TemplateTarget(
                template=template,
                url=f"/gallery/{image.caption.lower()}.html",
                render_kwargs={
                    "img_url": copy_target.url,
                    "img_caption": image.caption,
                },
            )
            targets.append(copy_target)
            targets.append(template_target)

        md_eng = MarkdownEngine(self.config, self.theme)
        targets.extend(md_eng.create_targets())

        return targets

    def get_sources(self) -> list[ImageSource]:
        imgs_dirname = "gallery"
        lists_file_path = self.source_dir / imgs_dirname / "imgs.yaml"

        with lists_file_path.open() as src:
            return [
                ImageSource(
                    path=self.source_dir / imgs_dirname / entry["filename"],
                    caption=entry["caption"],
                )
                for entry in yaml.safe_load(src)
            ]
