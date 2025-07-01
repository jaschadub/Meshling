"""Tab widgets for the enhanced UI architecture."""

from meshling.ui.widgets.tabs.base_tab import BaseTab, TabPlaceholder
from meshling.ui.widgets.tabs.channels_tab import ChannelsTab
from meshling.ui.widgets.tabs.config_tab import ConfigTab
from meshling.ui.widgets.tabs.messages_tab import MessagesTab
from meshling.ui.widgets.tabs.nodes_tab import NodesTab
from meshling.ui.widgets.tabs.packets_tab import PacketsTab
from meshling.ui.widgets.tabs.tab_container import TabContainer

__all__ = [
    "BaseTab",
    "TabPlaceholder",
    "TabContainer",
    "ChannelsTab",
    "NodesTab",
    "PacketsTab",
    "ConfigTab",
    "MessagesTab",
]
