# Volt custom plugin

from volt.plugin.core import Plugin


class MyPlugin(Plugin):

    # Uncomment to set a default set of plugin configuration values
    #DEFAULTS = Config(
    #)

    # Uncomment to set the plugin entry name in voltconf
    #USER_CONF_ENTRY = ''

    def run(self):
        pass
