# -*- coding: utf-8 -*-

# Pokémanki
# Copyright (C) 2022 Exkywor and zjosua

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from bs4 import BeautifulSoup
from typing import Any, Tuple

import aqt
from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import askUser

from .config import get_synced_conf, init_config
from .display import pokemon_display
from .gui.pokemanki_options import invoke_pokemanki_options
from .pokemon import *
from .tags import Tags
from .trades import Trades
from .utils import pkmnimgfolder


# global definition of statsDialog for hooks and async callback function
statsDialog = None

tradeclass = object()
tags = object()

# Add images and CSS to media server
mw.addonManager.setWebExports(
    __name__, r"(pokemon_images|progress_bars|pokemanki_css)/.*(css|png)"
)


def build_menu() -> None:
    global tradeclass

    # Make actions for settings and reset
    nicknameaction = QAction("&Nicknames", mw)
    resetaction = QAction("&Reset", mw)
    tradeaction = QAction("&Trade", mw)
    toggleaction = QAction("&Decks vs. Tags", mw)
    tagsaction = QAction("&Tags", mw)
    prestigeaction = QAction("&Prestige Pokémon", mw)
    unprestigeaction = QAction("&Unprestige Pokémon", mw)
    everstoneaction = QAction("&Give Everstone", mw)
    uneverstoneaction = QAction("&Take Everstone", mw)
    megastoneaction = QAction("&Give Mega Stone", mw)
    unmegastoneaction = QAction("&Take Mega Stone", mw)
    alolanaction = QAction("&Give Alolan Passport", mw)
    unalolanaction = QAction("&Take Alolan Passport", mw)
    bottomaction = QAction("Move Pokémon to &Bottom", mw)
    topaction = QAction("Move Pokémon to &Top", mw)
    settingsaction = QAction("&Settings", mw)

    # Connect actions to functions
    tradeclass = Trades()
    tags = Tags()
    qconnect(nicknameaction.triggered, nickname)
    qconnect(resetaction.triggered, reset_pokemanki)
    qconnect(tradeaction.triggered, tradeclass.open)
    qconnect(toggleaction.triggered, Toggle)
    qconnect(tagsaction.triggered, tags.tagMenu)
    qconnect(prestigeaction.triggered, PrestigePokemon)
    qconnect(unprestigeaction.triggered, UnprestigePokemon)
    qconnect(everstoneaction.triggered, giveEverstone)
    qconnect(uneverstoneaction.triggered, takeEverstone)
    qconnect(megastoneaction.triggered, giveMegastone)
    qconnect(unmegastoneaction.triggered, takeMegastone)
    qconnect(alolanaction.triggered, giveAlolanPassport)
    qconnect(unalolanaction.triggered, takeAlolanPassport)
    qconnect(bottomaction.triggered, MovetoBottom)
    qconnect(topaction.triggered, MovetoTop)
    qconnect(settingsaction.triggered, invoke_pokemanki_options)

    mw.pokemenu.clear()

    mw.form.menuTools.addMenu(mw.pokemenu)
    mw.pokemenu.addAction(toggleaction)
    mw.pokemenu.addAction(nicknameaction)
    mw.prestigemenu = QMenu("&Prestige Menu", mw)
    mw.pokemenu.addMenu(mw.prestigemenu)
    mw.prestigemenu.addAction(prestigeaction)
    mw.prestigemenu.addAction(unprestigeaction)

    f = get_synced_conf()["decks_or_tags"]
    if f == "tags":
        mw.pokemenu.addAction(tagsaction)
    else:  # Not yet implemented for tagmon
        mw.everstonemenu = QMenu("&Everstone", mw)
        mw.pokemenu.addMenu(mw.everstonemenu)
        mw.everstonemenu.addAction(everstoneaction)
        mw.everstonemenu.addAction(uneverstoneaction)
        mw.megastonemenu = QMenu("&Mega Stone", mw)
        mw.pokemenu.addMenu(mw.megastonemenu)
        mw.megastonemenu.addAction(megastoneaction)
        mw.megastonemenu.addAction(unmegastoneaction)
        mw.alolanmenu = QMenu("&Alolan Passport", mw)
        mw.pokemenu.addMenu(mw.alolanmenu)
        mw.alolanmenu.addAction(alolanaction)
        mw.alolanmenu.addAction(unalolanaction)
        mw.pokemenu.addAction(tradeaction)

    mw.pokemenu.addAction(resetaction)
    mw.pokemenu.addAction(settingsaction)


# Wrap pokemon_display function of display.py with the todayStats function of anki.stats.py
# Note that above comment *may* be outdated
display_func = pokemon_display


def message_handler(
    handled: Tuple[bool, Any], message: str, context: Any
) -> Tuple[bool, Any]:
    # https://github.com/ankitects/anki/blob/main/qt/tools/genhooks_gui.py#L618
    if not type(context) == aqt.stats.NewDeckStats:
        return handled
    if not message.startswith("Pokemanki#"):
        return handled
    f = get_synced_conf()["decks_or_tags"]
    if message == "Pokemanki#currentDeck":
        html = pokemon_display(f, False).replace("`", "'")
    elif message == "Pokemanki#wholeCollection":
        html = pokemon_display(f, True).replace("`", "'")
    else:
        starts = "Pokemanki#search#"
        term = message[len(starts) :]
        # Todo: implement selective
        return (True, None)
    statsDialog.form.web.eval(f"Pokemanki.setPokemanki(`{html}`)")
    return (True, None)


def _onStatsOpen(dialog: aqt.stats.NewDeckStats) -> None:
    global statsDialog
    statsDialog = dialog
    js = (addon_dir / "web.js").read_text(encoding="utf-8")
    statsDialog.form.web.eval(js)


def onStatsOpen(statsDialog: aqt.stats.NewDeckStats) -> None:
    statsDialog.form.web.loadFinished.connect(lambda _: _onStatsOpen(statsDialog))


def replace_gears(
    deck_browser: aqt.deckbrowser.DeckBrowser,
    content: aqt.deckbrowser.DeckBrowserContent,
) -> None:
    conf = get_synced_conf()
    if not conf:
        return
    pokemons = conf["pokemon_list"]
    soup = BeautifulSoup(content.tree, "html.parser")
    for tr in soup.select("tr[id]"):
        deck_id = int(tr["id"])
        name = next((pokemon[0] for pokemon in pokemons if pokemon[1] == deck_id), None)
        if name:
            tr.select("img.gears")[0]["src"] = f"{pkmnimgfolder}/{name}.png"
            tr.select("img.gears")[0]["class"] = "gears pokemon"
    style = soup.new_tag("style")
    style.string = ".gears.pokemon{filter:none;opacity:1}"
    soup.append(style)
    content.tree = soup


def remove_config(dialog: aqt.addons.AddonsDialog, addons: List[str]) -> None:
    for name in ["1041307953", "pokemanki"]:
        if name in addons:
            delete_pokemanki_conf = askUser(
                """\
The Pokémanki add-on will be deleted.
Do you want to remove its config too?
This will delete your Pokémon.
""",
                parent=dialog,
                title="Remove Pokémanki config?",
            )
            if delete_pokemanki_conf:
                mw.col.remove_config("pokemanki")


def pokemanki_init() -> None:
    init_config()
    mw.pokemenu = QMenu("&Pokémanki", mw)
    build_menu()
    gui_hooks.deck_browser_will_render_content.append(replace_gears)
    gui_hooks.addons_dialog_will_delete_addons.append(remove_config)


def delayed_init() -> None:
    mw.progress.single_shot(50, pokemanki_init)


gui_hooks.profile_did_open.append(delayed_init)
gui_hooks.stats_dialog_will_show.append(onStatsOpen)
gui_hooks.webview_did_receive_js_message.append(message_handler)
