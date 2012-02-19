# Volt configurations file

from volt.config.base import Config


# General site configurations
SITE = Config(

  # Your site name
  TITLE = "Volt Demo",

  # Your site URL
  URL = "http://127.0.0.1",

  # Your site description
  DESC = "Because static sites have potential",

  # Engines used in generating the site
  # Available engines are 'page', 'blog', and 'collection'
  # To disable an engine, just remove its name from this list
  ENGINES = ['page', 'blog', ],
)
