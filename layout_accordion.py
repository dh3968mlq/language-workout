from dash import html
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import pandas as pd
from math import log10, floor
import layout_main_screen

def cre_accordion(langspec, engine, adminuser = False):
    result = dmc.Accordion(
            chevronPosition="right",
            variant="contained",
            disableCollapse=True,  # for dmc 3.0
            children=[
                dmc.AccordionItem(
                    [
                        dmc.AccordionControl(
                            dmc.Group(
                                [
                                    DashIconify(icon="flat-color-icons:collaboration", width=30),
                                    dmc.Title(f"Language Workout", order=2),
                                ]
                            )                            
                        ),
                        dmc.AccordionPanel(
                            [
                                dmc.Text("An app to help learning foreign words. It prompts with a randomly "+
                                     "chosen word, then you click to reveal the English. " +
                                     "Choose a smaller vocab size to get more common words. " + 
                                     "Clicking 'focus' makes a word return more often. " +
                                     "The Japanese is beginner level, kana only, no kanji"
                                    ),
                                dmc.Space(h=6),
                                dmc.Text("This site is non-commercial, "+
                                        "has no adverts and collects no personal " +
                                        "data. Your focussed words are stored on your device"),
                                dmc.Space(h=6),
                                dmc.Text([
                                    'The site is provided "as is", without warranty of any kind, express or ' +
                                    "implied."
                                ]),
                                dmc.Space(h=6),
                                dmc.Text([
                                    'Built using ',
                                    dmc.Anchor(
                                        "Dash",
                                        href="https://dash.plotly.com/",
                                        target="_blank",
                                    ),
                                    ' and ',
                                    dmc.Anchor(
                                        "DMC",
                                        href="https://www.dash-mantine-components.com/",
                                        target="_blank",
                                    )
                                ]),
                            ],
                            keepMountedMode="display-none",
                        )
                    ],
                    value="header-item",
                )                
            ] + 
            [
                dmc.AccordionItem(
                    [
                        create_accordion_label(lspec, engine),
                        dmc.AccordionPanel(
                            layout_main_screen.layout_main_screen(
                                prefix=f"{lid}-",
                                lspec=lspec,
                                engine=engine,
                                adminuser = adminuser
                            ),
                            keepMountedMode="display-none",
                        ),
                    ],
                    value=f"{lid}-item",
                ) for lid, lspec in langspec.items()
            ],
            value="header-item", # f"{next(iter(langspec))}-item",  # Gets first key in the dictionary
            id=f"main-accordion",
            styles={"label":{"padding-top":"4px", "padding-bottom":"4px"}}
        )
    return result 

def create_accordion_label(lspec, engine):
    with engine.connect() as conn:
        dfn = pd.read_sql(f"""select count(1) from {lspec['table']} 
                where not fwd_ignore 
                    and not fwd_noncore""",
                conn
                )
    nwords = dfn["count"][0]
    power = floor(log10(nwords/3))
    nwords = round(nwords, -power)
        
    return dmc.AccordionControl(
        dmc.Group(
            [
                DashIconify(icon=lspec["icon"], width=30),
                html.Div(
                    [
                        dmc.Title(f"{lspec['language'].capitalize()} / English", order=2),
                        dmc.Text(f"{nwords} words and phrases", size="sm", 
                                 style={"fontWeight": 400, "color":"DimGrey"}), #fw=400, c="dimmed"),
                    ]
                ),
            ]
        ),
    )

