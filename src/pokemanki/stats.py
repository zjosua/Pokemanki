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

from typing import List, Tuple

import anki
from anki.utils import ids2str
from aqt import mw

from .config import get_synced_conf
from .utils import *


def cardIdsFromDeckIds(queryDb: anki.dbproxy.DBProxy, deckIds: List[int]) -> List[int]:
    query = f"select id from cards where did in {ids2str(deckIds)}"
    cardIds = [i[0] for i in queryDb.all(query)]
    return cardIds


def cardInterval(queryDb: anki.dbproxy.DBProxy, cid: int, startdate: int) -> int:
    revLogIvl = queryDb.scalar(
        f"SELECT ivl FROM revlog WHERE id >= {startdate} AND cid = {cid} "
        "ORDER BY id DESC LIMIT 1 OFFSET 0"
    )
    ctype = queryDb.scalar(
        f"SELECT type FROM cards WHERE id = {cid} ORDER BY id DESC LIMIT 1 OFFSET 0"
    )

    # card interval is "New"
    if ctype == 0:
        ivl = 0
    elif revLogIvl is None:
        ivl = 0
    elif revLogIvl < 0:
        # Anki represents "learning" card review log intervals as negative minutes
        # So, convert to days
        ivl = revLogIvl * -1 / 60 / 1440
    else:
        ivl = revLogIvl

    return ivl


def deckStats(deck_ids: List[int]) -> List[Tuple[int, int]]:
    """
    deck_ids: list
    returns [(card_id, card_interval), ...]
    """
    cardIds = cardIdsFromDeckIds(mw.col.db, deck_ids)

    # result = self.col.db.all("""select id, ivl from cards where did in %s""" %
    #             ids2str(self.col.decks.active()))
    global_startdate = get_synced_conf().get("global_startdate", 1160006400000)
    result = []
    for cid in cardIds:
        ivl = cardInterval(mw.col.db, cid, global_startdate)
        result.append((cid, ivl))

    return result


def MultiStats(wholeCollection: bool) -> List[Tuple[int, List[Tuple[int, int]]]]:
    """Retrieve id and ivl for each subdeck that does not have subdecks itself

    :param bool wholeCollection:
    :return: List of tuples with decks and their cards (deck_id, [(card_id, interval), ...])
    :rtype: List
    """
    # Get list of subdecks
    if wholeCollection:
        # Get results for all subdecks in collection
        alldecks = mw.col.decks.all_names_and_ids()
        # Determine which subdecks do not have their own subdecks
        nograndchildren = []
        for item in alldecks:
            if len(mw.col.decks.children(int(item.id))) == 0:
                nograndchildren.append(int(item.id))
    else:
        # Get results only for all subdecks of selected deck
        curr_deck = mw.col.decks.active()[0]
        children = mw.col.decks.children(curr_deck)
        if not children:
            nograndchildren = [curr_deck]
        else:
            childlist = [item[1] for item in children]
            # Determine which subdecks do not have their own subdecks
            nograndchildren = []
            for item in childlist:
                if len(mw.col.decks.children(item)) == 0:
                    nograndchildren.append(item)
    resultlist = []
    # Find results for each card in these decks
    for item in nograndchildren:
        resultlist.append(deckStats([item]))
    # Zip the deck ids with the results
    nograndchildresults = list(zip(nograndchildren, resultlist))

    return nograndchildresults


def TagStats() -> List[Tuple[str, List[List[int]]]]:
    "Returns List[(tag_name, [[card_id, card_interval], ...]), ...]"
    savedtags = get_synced_conf()["tags"]
    resultlist = []
    for item in savedtags:
        result = mw.col.db.all(
            "select c.id, c.ivl from cards c, notes n where c.nid = n.id and n.tags LIKE '%"
            + item
            + "%'"
        )
        resultlist.append(result)
    results = list(zip(savedtags, resultlist))
    return results
