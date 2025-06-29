from aqt import mw
from aqt.gui_hooks import top_toolbar_did_init_links
from aqt.toolbar import Toolbar
from ..ui.streak_popup import open_streak_popup_with_manager
from ..ui.freeze_popup import open_freeze_popup


def setup_toolbar():
    def _create_styled_link(toolbar: Toolbar, name: str, label: str, callback, tip: str, class_name: str) -> str:
        link = toolbar.create_link(name, label, callback, tip)
        return link.replace(
            '<a ',
            f'<a class="{class_name}" style="text-decoration:none; padding:4px; align-items:center; gap:4px; border-radius:4px;" ', 1
        )

    def on_top_toolbar_did_init_links(links: list[str], toolbar: Toolbar):
        streak_label = getattr(mw, "streak_button_text", "Streak")
        streak_link = _create_styled_link(
            toolbar, 
            "my_streak_popup", 
            streak_label, 
            lambda: open_streak_popup_with_manager(mw), 
            "View streak stats", 
            "streak-link"
        )

        freeze_label = getattr(mw, "freeze_button_text", "Freezes")
        freeze_link = _create_styled_link(
            toolbar, 
            "my_freeze_popup", 
            freeze_label, 
            lambda: open_freeze_popup(mw), 
            "View freeze stats", 
            "freeze-link"
        )

        hover_style = """
        <style>
        a.streak-link:hover, a.freeze-link:hover {
            background-color: #323232;
            cursor: pointer;
        }
        </style>
        """

        links.append(hover_style)
        links.append(streak_link)
        links.append(freeze_link)

    top_toolbar_did_init_links.append(on_top_toolbar_did_init_links)
