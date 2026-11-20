import os
from sqlalchemy import create_engine
from dash import Dash, _dash_renderer
import dash_mantine_components as dmc
import callbacks_main_screen
import callbacks_find_word
import callbacks_vocab_lists
import callbacks_vocab_list_add

import gunicorn
import layout_accordion
import layout_find_word
import layout_vocab_lists
import layout_vocab_list_add
import langspecs

_dash_renderer._set_react_version("19.2.4")  # For DMC 3.0
app = Dash(__name__)
app.title = "Language Workout"
app._favicon = "favicon.png"
server = app.server

# -- Selection between superuser and ordinary user
# -- With this approach, nobody is logging in
# -- It's the instance of the application that is one or the other
adminuser = (os.getenv("LWADMIN") == "TRUE")

# This is available on Heroku
database_url = os.getenv("DATABASE_URL")
if database_url:
    connectionstring = database_url.replace("postgres","postgresql+psycopg2", 1)
    engine = create_engine(connectionstring)
elif adminuser:
    engine = create_engine(f"postgresql+psycopg2://pi:{os.getenv('PGPW')}@pi5a:5432/languages")
else:
    engine = create_engine(f"postgresql+psycopg2://user:{os.getenv('PGUSERPW')}@pi5a:5432/languages")

langspecs = langspecs.get_langspecs()

# --------------------------------------------------------------------------------------
app.layout = dmc.MantineProvider(
    children=dmc.Container(
        size='sm',
        children=
        [
            layout_accordion.cre_accordion(langspecs, engine, adminuser=adminuser),
        ] +
        [
            layout_find_word.cre_layout_find_word(prefix=langid + "-", lspec=lspec) for langid, lspec in langspecs.items()
        ] + 
        [
            layout_vocab_lists.cre_layout_vocab_lists(prefix=langid + "-", lspec=lspec) for langid, lspec in langspecs.items()
        ] + 
        [
            layout_vocab_list_add.cre_layout_add_vocab_list(prefix=langid + "-") for langid in langspecs
        ],
    )
)
# -------------------------------------------------------------------
for lid, lspec in langspecs.items():
    prefix=f"{lid}-"
    callbacks_main_screen.cre_callbacks(app, engine, prefix=prefix, lspec=lspec, adminuser=adminuser)
    callbacks_find_word.cre_callbacks(app, engine, prefix=prefix, lspec=lspec, adminuser=adminuser)
    callbacks_vocab_lists.cre_callbacks(app, engine, prefix=prefix, lspec=lspec, adminuser=adminuser)
    callbacks_vocab_list_add.cre_callbacks(app, engine, prefix=prefix, lspec=lspec, adminuser=adminuser)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="8050")
