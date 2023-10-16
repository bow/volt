from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import yaml
from volt import Engine, CopyOutput, TemplateOutput
from volt.engines import MarkdownEngine


@dataclass
class ImageSource:
    caption: str
    path: Path


class GalleryEngine(Engine):
    def prepare_outputs(
        self, with_draft: bool
    ) -> Sequence[TemplateOutput | CopyOutput]:
        outputs: list[TemplateOutput | CopyOutput] = []

        template = self.theme.load_template_file("image.html.j2")

        for image in self.list_img_sources():
            copy_outputs = CopyOutput(
                src=image.path,
                url_parts=("assets", "imgs", image.path.name),
            )
            template_outputs = TemplateOutput(
                template=template,
                url=f"/gallery/{image.caption.lower()}.html",
                render_kwargs={
                    "img_url": copy_outputs.url,
                    "img_caption": image.caption,
                },
            )
            outputs.append(copy_outputs)
            outputs.append(template_outputs)

        md_eng = MarkdownEngine(self.config, self.theme)
        outputs.extend(md_eng.prepare_outputs(with_draft))

        return outputs

    def list_img_sources(self) -> list[ImageSource]:
        imgs_dirname = "gallery"
        lists_file_path = self.contents_dir / imgs_dirname / "imgs.yaml"

        with lists_file_path.open() as src:
            return [
                ImageSource(
                    path=self.contents_dir / imgs_dirname / entry["filename"],
                    caption=entry["caption"],
                )
                for entry in yaml.safe_load(src)
            ]
