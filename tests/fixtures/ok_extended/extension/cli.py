from volt.cli import xcmd


@xcmd.command(name="hello-ext")  # type: ignore[attr-defined]
def hello_ext() -> None:
    """Custom CLI command extension"""
    print("FooBar!")
