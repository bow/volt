from volt import hooks, CopyTarget, FileTarget, Site


@hooks.pre_site_write
def modify_css(_, site: Site) -> None:

    theme = site.theme
    hook_config = theme.get_hook_config(hooks.name())

    modified_css_url = hook_config["modified_css_url"]

    if not theme.hook_enabled(hooks.name()):
        hooks.log().debug("skipping disabled hook")
        return None

    css_targets = [
        target
        for target in sorted(
            site.extract_targets("*.css"),
            key=lambda target: target.url,
        )
        if isinstance(target, CopyTarget)
    ]
    if not css_targets:
        hooks.log().debug("no targets found for hook")
        return None

    hooks.log().debug(
        "found targets for hook",
        num_targets=len(css_targets),
        target_urls=[target.url for target in css_targets],
    )

    modified = "\n".join([target.src.read_text() for target in css_targets])
    modified += "\np { color: DarkRed; }"
    modified_target = FileTarget(url=modified_css_url, contents=modified)
    site.targets.append(modified_target)

    return None
