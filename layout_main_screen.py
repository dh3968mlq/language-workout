from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import pandas as pd

def layout_main_screen(prefix, lspec, engine, adminuser=False):
    'Main layout for each panel'
    
    btn_get_foreign_word_label = f"Get {lspec['language'].capitalize()}"
    texthoverfunction = lspec.get("texthoverfunction", None)

    # Find how many words
    with engine.connect() as conn:
        dfn = pd.read_sql(f"""select count(1) from {lspec['table']} 
                where not fwd_ignore 
                    and not fwd_noncore""",
                conn
                )
    nwords = dfn["count"][0]
    wordcounts = [x for x in ["100","250","500","1000","2500","5000", "10000"] if int(x) < nwords]
    alltext = "All"   # not f"All {nwords}", which looks ugly
    wordcounts.append(alltext)

    lfe = html.Div(children=
        [
            dcc.Store(id=prefix + "root-store-words", storage_type="session", data=[]),
            dcc.Store(id=prefix + "root-store-selected-word", storage_type="session", data=[]),
            # fw-store-context rightly belongs in find word, but we cannot place it inside a dmc.Modal?
            dcc.Store(id=prefix + "fw-store-context", storage_type="session", data=[]), 
            dcc.Store(id=prefix + "root-store-focussed", storage_type="local", data=[]),
            dmc.Group(
                children=[
                    dmc.Select(
                        placeholder="Vocab size",
                        id=prefix+"root-select-nwords",
                        value=alltext,
                        label="Vocab size",
                        data=wordcounts,
                        w='100px', 
                        persistence=True, persistence_type="session",
                        clearable=False,
                        allowDeselect=False,
                    ),
                    dmc.Select(
                        placeholder="Show what",
                        id=prefix+"root-select-show-what",
                        value="All",
                        label="Show",
                        data=[],
                        w='200px', 
                        persistence=True, persistence_type="session",
                        clearable=False,
                        allowDeselect=False,
                    ),
                    dmc.Checkbox(label="Include non-core", id=prefix+"root-chk-incnoncore", 
                                 style={"justify":"flex-end"} if adminuser else {"justify":"flex-end", "display":"none"}, 
                                 checked=False
                                 ),
                    dmc.Button(children="Lists...", 
                                id=prefix+"root-vl-button-lists", size="xs",
                                style={} if adminuser else {"display":"none"},
                               ),
                ],
                mb=10
            ),
            dmc.Grid(
                align='center',
                gap="xs",
                children=[
                    dmc.GridCol(
                        dmc.Button(children=btn_get_foreign_word_label, 
                                   id=prefix+"root-button-get-foreign-word", size="xs"),
                        span="content"
                    ),
                    dmc.GridCol(
                        children=[
                            dmc.HoverCard(
                                withArrow=True,
                                shadow="md",
                                disabled = not texthoverfunction,
                                position="right",
                                events={"touch":True}, # Show hover on touch on phones / tablets
                                children=[
                                    dmc.HoverCardTarget(dmc.Text(children="<Get word>", id=prefix+"root-foreign-text"),),
                                    dmc.HoverCardDropdown(
                                        dmc.Text(
                                            children="...",
                                            id=prefix+"root-text-hovercarddropdown",
                                            size="sm",
                                        )
                                    ),
                                ],
                            ) 
                        ],
                        span="auto"
                    ),
                    dmc.GridCol(
                        dmc.Tooltip(
                            dmc.ActionIcon(
                                DashIconify(icon="ant-design:search-outlined", width=20),
                                id=prefix+"root-fw-button-search", size="md"
                            ),
                            label="Find word(s)"
                        ),
                        span="content",
                        #px="2px",
                    ),
                    dmc.GridCol(
                        dmc.Anchor(
                            dmc.Tooltip(
                                dmc.ActionIcon(
                                    DashIconify(icon="material-symbols-light:dictionary-rounded", width=20),
                                    size="md"
                                ),
                                label= "Jisho lookup" if prefix == "jp-" else "Wordreference lookup"
                            ),
                            href="https://jisho.org/" if prefix == "jp-" else "https://www.wordreference.com/",
                            id=prefix+"root-dictionary-lookup",
                            target="_self",
                        ),
                        span="content",
                        #px="2px",
                    ),
                ]
            ),
            dmc.Space(h=18),
            dmc.Grid(
                children=[
                    dmc.GridCol(
                        dmc.Button(children="Get English", id=prefix+"root-button-get-english", size="xs"),
                        span="content"
                    ),
                    dmc.GridCol(
                        dmc.Textarea(value="", id=prefix+"root-english-text",w="100%",
                                     autosize=True, readOnly=not adminuser),
                        span="auto"
                    ),
                ]
            ),
            dmc.Space(h=10),
            dmc.Group(
                children=[
                    dmc.Textarea(
                        value="", id=prefix+"root-text-notes", autosize=True,
                        label="Notes", mb=10,
                        w='100%', readOnly=not adminuser,
                    ),
                ]
            ),
            dmc.Grid(
                align='center',
                children=[
                    dmc.GridCol(
                        dmc.Group(
                            children=[
                                dmc.Checkbox(label="Focus", id=prefix+"root-chk-focus"),
                                dmc.Checkbox(label="Non-core", id=prefix+"root-chk-noncore",
                                             style={} if adminuser else {"display":"none"}),
                            ]
                        ),
                        span="auto"
                    ),
                    dmc.GridCol(
                        dmc.Text(id=prefix+'root-txt-corpusfreq', style={"justify":"flex-end"}),
                        span="content"
                    )
                ],
            ),
            dmc.Space(h=10),
            dmc.Button(children="Upload to database", id=prefix+"root-button-gupload", size="xs",
                       style={} if adminuser else {"display":"none"}), 
        ]
    )
    return lfe
