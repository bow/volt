# Volt configurations file

from volt.config.base import Config


# General site configurations
SITE = Config(

  # Your site name
  TITLE = "Volt Demo",

  # Your site URL (no need to include 'http://')
  URL = "localhost",

  # Your site tagline / description
  DESC = "Because static sites have potential",
)

# Engines switch; sets whether an engine is used in site generation or not
ENGINES = Config(

  BLOG = True,
  PAGE = True,
)
