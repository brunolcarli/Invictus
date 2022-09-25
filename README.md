<table align="center"><tr><td align="center" width="9999">

<img src="https://pbs.twimg.com/media/FEAAFyrX0AQghlp.jpg" align="center" width="300" alt="Project icon">

# Invictus
## Back-End API

*Ogame data tracker*

[![Run on Repl.it](https://replit.com/badge/github/brunolcarli/Invictus)](https://invictus.brunolcarli.repl.co/graphql/?query=query%7B%0A%20%20__schema%7B%0A%20%20%20%20types%20%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20fields%20%7B%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20type%7Bkind%20ofType%20%7B%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%7D%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D)

</td></tr></table>


The [Invictus](https://foundation.fandom.com/wiki/Invictus) API aims to crawl data from [Ogame](https://lobby.ogame.gameforge.com/pt_BR/hub) universe frm time to time with purposes of store statistical data over time from player growth ingame. All collected data is originally gathered from ogame gameforge API and stored in a relational database. No data exposed goes against game rules and are intended for statistical and tactical use only.

Currently the only universe (Ogame server) explored is the `br144`.