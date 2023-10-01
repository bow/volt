from volt import hooks, CopyOutput, FileOutput, Site


@hooks.pre_site_write
def modify_css(_, site: Site) -> None:

    theme = site.theme
    hook_config = theme.get_hook_config(hooks.name())

    modified_css_url = hook_config["modified_css_url"]

    if not theme.hook_enabled(hooks.name()):
        hooks.log().debug("skipping disabled hook")
        return None

    css_outputs = [
        output
        for output in sorted(
            site.extract_outputs("*.css"),
            key=lambda output: output.url,
        )
        if isinstance(output, CopyOutput)
    ]
    if not css_outputs:
        hooks.log().debug("no CSS outputs found for modification")
        return None

    hooks.log().debug(
        "found CSS outputs to be modified",
        num_outputs=len(css_outputs),
        output_urls=[output.url for output in css_outputs],
    )

    modified = "\n".join([output.src.read_text() for output in css_outputs])
    modified += "\np { color: DarkRed; }"
    modified_output = FileOutput(url=modified_css_url, contents=modified)
    site.outputs.append(modified_output)

    return None
