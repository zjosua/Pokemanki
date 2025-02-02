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

import os
import random
import shutil
from typing import List, Tuple, Union

from aqt import mw

from .compute import MultiPokemon, TagPokemon
from .config import get_local_conf
from .utils import *


def pokemon_display(decks_or_tags: str, wholecollection: bool = True) -> str:
    """
    Control the generation of the html code to display.

    :param str decks_or_tags: Whether Pokémon are assigned by decks or by tags.
    :param bool wholecollection: True if multiple Pokémon, false if single.
    :return: The html text to display.
    :rtype: str
    """

    # Get list of Pokémon from tags or decks.
    #   For decks, if wholeCollection, get all assigned Pokémon and assign to Pokémon,
    #   else, show Pokémon for either single deck or all subdecks and store in Pokémon
    if decks_or_tags == "tags":
        pokemon = TagPokemon()
    else:
        pokemon = MultiPokemon(wholecollection)

    result = _show(pokemon)

    return result


def _show(
    data: Union[
        Union[
            List[Union[Tuple[str, int, float, str], Tuple[str, int, float]]],
            None,
        ],
        Union[
            List[Union[Tuple[str, str, float, str], Tuple[str, str, float]]],
            None,
        ],
    ]
) -> str:
    """
    Generate the html to inject into the new stats window.

    :param List|None data: Pokémon information.
    :return: The html code to display.
    :rtype: str
    """

    if not data:
        return ""

    # Pokemanki container header
    txt = (
        '<h1 style="text-align: center; font-weight: 700; margin-top: 40px;">Pokémon</h1>'
        '<div style="text-align: center;">Your Pokémon</div>'
    )

    # If single Pokémon, show centered card
    if type(data) == tuple:
        txt += '<div class="pk-st-single">'
        txt += _card_html(data[0], data[1], data[2], data[3] if len(data) == 4 else "")
    # If multiple Pokémon, show flex row of cards
    elif type(data) == list:
        if len(data) == 1:
            txt += '<div class="pk-st-single">'
            multi = False
        else:
            conf = get_local_conf()
            card_flow = conf.get("align_cards", "wrap")
            if card_flow == "wrap":
                txt += '<div class="pk-st-container">'
            elif card_flow == "hscroll":
                txt += '<div class="pk-st-container" style="flex-wrap: nowrap; \
                        justify-content: flex-start;">'
            multi = True

        sortedData = sorted(data, key=lambda k: k[2], reverse=True)
        for pokemon in sortedData:
            txt += _card_html(
                pokemon[0],
                pokemon[1],
                pokemon[2],
                pokemon[3] if len(pokemon) == 4 else "",
                multi,
            )

    # Close cards container
    txt += "</div>"

    # Pokémon total
    txt += f'<h4 style="text-align: center; margin-top: 5px;"><b>Total:</b> {len(data)} Pokémon</h4>'

    # Return txt
    return txt


def _card_html(
    name: str,
    source: Union[int, str],
    level: float,
    nickname: str = "",
    multi: bool = False,
) -> str:
    """
    Generate the html text for a Pokémon card.

    :param str name: Name of the Pokémon.
    :param int|str source: Id of the deck or name of the tag the Pokémon belongs to.
    :param float level: The Pokémon's lvl.
    :param str nickname: Pokémon's nickname, if it has any.
    :param bool multi: True if multiple Pokémon are being rendered.
    :return: The card html.
    :rtype: str
    """
    # Start card
    card = f'<div class="pk-st-card {"pk-st-shrink" if multi else ""}">'

    #############
    # Head info
    #############
    card += (
        '<div class="pk-st-card-info" style="margin-bottom: auto;">'
        '<div class="pk-st-card-top">'
    )
    # Name and deck
    card += (
        '<div class="pk-st-card-name">'
        f'<span><b>{nickname if nickname != "" else name}</b></span>'
        f"<span><i>{_get_source_name(source)}</i></span>"
        "</div>"
    )
    # Level
    card += (
        '<div class="pk-st-card-lvl">'
        '<span style="text-align: right;">Lvl</span>'
        '<span style="text-align: right;">'
        f'<b>{int(level-50) if _in_list("prestige", source) else int(level)}</b>'
        "</span>"
        "</div>"
        "</div>"
    )
    # Divider and end of top info
    card += '<div class="pk-st-divider" style="margin-top: 10px;"></div>' "</div>"

    #############
    # Image
    #############
    card += f'<img src="{pkmnimgfolder}/{_image_name(name, source)}.png" class="pk-st-card-img"/>'

    #############
    # Bottom info
    #############
    card += (
        '<div class="pk-st-card-info" style="margin-top: auto;">'
        '<div class="pk-st-divider" style="margin-bottom: 10px;"></div>'
    )
    # Held/SP
    held = _held_html(source)
    if held != "":
        card += '<div class="pk-st-card-sp">' "<span><b>SP: </b></span>"
        card += held
        card += "</div>"
    # Progress bar
    if name == "Egg":
        card += f'<span class="pk-st-card-xp">{_egg_hatch_text(level)}</span>'
    else:
        card += f'<img src="/_addons/{addon_package}/progress_bars/{_calculate_xp_progress(level)}.png" class="pk-st-card-xp"/>'
    card += "</div>"

    # End card
    card += "</div>"

    # TODO: Add # of Pokémon
    # Make bottom line using function from stats.py and assign to text_lines
    # line( text_lines, "<b>Total</b>", "</b>%s Pokémon<b>" % _num_pokemon)

    return card


def _get_source_name(item: Union[int, str]) -> str:
    """
    Get the name of the tag or deck based on the input item.

    :param int item: Element to find the source of
    :return: The name of the deck
    """

    if isinstance(item, int):
        return mw.col.decks.name(item)
    else:
        return item


def _in_list(listname: str, item: str) -> bool:
    """
    Check if an item is in a list.

    :param str listname: Name of the list to check in.
    :param str item: Item to find in the list
    :return: True if the list exists and the item is in it, otherwise false.
    :rtype: bool
    """

    if listname not in ["prestige", "everstone", "megastone", "alolan"]:
        return False

    return item in get_synced_conf()[f"{listname}list"]


def _image_name(name: str, source: Union[int, str]) -> str:
    """
    Get the image name based on the Pokémon's name and any special attributes.

    :param str name: Pokémon's name.
    :param int|str source: Id of the deck or tag name the Pokémon belongs to.
    :return: The image name to be used to retrieve it.
    :rtype: str
    """

    pkmnimgfolder = addon_dir / "pokemon_images"

    fullname = name
    if _in_list("everstone", source):
        # FIX: name is never declared!u
        if name == "Pikachu":
            fullname += "_Ash" + str(random.randint(1, 5))
    if _in_list("megastone", source):
        if any([name + "_Mega" in imgname for imgname in os.listdir(pkmnimgfolder)]):
            fullname += "_Mega"
            if name == "Charizard" or name == "Mewtwo":
                fullname += get_local_conf()["X_or_Y_mega_evolutions"]
    if _in_list("alolan", source):
        if any([name + "_Alolan" in imgname for imgname in os.listdir(pkmnimgfolder)]):
            fullname += "_Alolan"

    return fullname


def _egg_hatch_text(level: float) -> str:
    """
    Get the egg's hatch text.

    :param float level: The level of the egg.
    :return: The hatch text.
    :rtype: str
    """
    if level < 2:
        return "Needs a lot more time to hatch"
    elif level < 3:
        return "Will take some time to hatch"
    elif level < 4:
        return "Moves around inside sometimes"
    else:
        return "Making sounds inside"


def _calculate_xp_progress(level: float) -> int:
    """
    Calculate the xp progress for the xp bar based on the given level.

    :param float level: The level to base the calculations on.
    :return: The progress in the xp bar.
    :rtype: int
    """
    return int(float(20 * (float(level) - int(float(level)))))


def _held_html(source: Union[int, str]) -> str:
    """
    Generate the held html code for the given Pokémon.

    :param int|str source: Id of the deck or tag name the Pokémon belongs to.
    :return: The concatenation of all held items' html. Empty if it has no items.
    :rtype: str
    """

    held = ""
    everstone_html = f'<img src="{pkmnimgfolder}/item_Everstone.png" height="20px"/>'
    megastone_html = f'<img src="{pkmnimgfolder}/item_Mega_Stone.png" height="25px"/>'
    alolan_html = f'<img src="{pkmnimgfolder}/item_Alolan_Passport.png" height="25px"/>'

    if _in_list("prestige", source):
        held += "<span>Prestiged </span>"
    if _in_list("everstone", source):
        held += everstone_html
    if _in_list("alolan", source):
        held += alolan_html
    if _in_list("megastone", source):
        held += megastone_html

    return held
