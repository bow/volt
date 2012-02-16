# Volt configurations file
from volt.conf.options import Options


# General site configurations
SITE = Options(

  # Your site name
  TITLE = "Volt Demo",

  # Your site URL (no need to include 'http://')
  URL = "localhost",

  # Your site tagline / description
  DESC = "Because static sites have potential",
)

# Engines switch; sets whether an engine is used in site generation or not
ENGINES = Options(

  BLOG = True,
  PAGE = True,
)
