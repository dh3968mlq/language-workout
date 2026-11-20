'''
Callbacks for the find word modal
PARENT OF:
    none
CHILD OF:
    main screen (root)
    vocab lists (vl)
'''
from typing import Any
from dash import Input, Output, State, no_update, ctx, clientside_callback
import pandas as pd
import utils

def cre_callbacks(app, engine, prefix, lspec, adminuser=False):
    table = lspec["table"]
    language=lspec["language"]
    colheading = lspec["colheading"]

    outputs = [
        ("fw-aggrid-find","rowData"), ("fw-btn-select", "disabled"), 
        ("fw-find-text", "value"), ("fw-modal", "opened"),
        ("fw-segmented-lang", "value"), ("fw-segmented-within", "value"),
        ("fw-text-wordcount", "children"), ("fw-store-context","data"), 
        # -- PARENT outputs - vocab lists
        ("vl-aggrid-words", "rowData"), 
        ("vl-modal", "opened"),
        # -- PARENT outputs - main screen
        ("root-store-selected-word", "data") 
    ]
    inputs = [
        ("root-fw-button-search","n_clicks"), # -- On parent screen, part of the fw functional group
        ("vl-fw-btn-add-word","n_clicks"), # -- PARENT trigger, ditto
        ('fw-aggrid-find', 'cellDoubleClicked'), ("fw-aggrid-find","selectedRows"), 
        ("fw-btn-cancel","n_clicks"), ("fw-btn-select","n_clicks"),
        ("fw-find-text","value"), ("fw-modal", "opened"),
        ("fw-segmented-lang", "value"), ("fw-segmented-within", "value")
    ]
    states = [
        ("fw-store-context","data"), ("root-store-selected-word", "data"),
        ("vl-aggrid-words", "rowData")
    ]

    callback_outputs = (Output(prefix+elid, elprop, allow_duplicate=True) for (elid, elprop) in outputs)
    callback_inputs = (Input(prefix+elid,elprop) for (elid, elprop) in inputs)
    callback_states = (State(prefix+elid,elprop) for (elid, elprop) in states)

    @app.callback(*callback_outputs, *callback_inputs, *callback_states, prevent_initial_call=True)
    def find_word_callback(*args):
        dp, dr = utils.cb_collate(args, ltrim = len(prefix))
        trigger = ctx.triggered_id
        fulltrigger = ctx.triggered[0]["prop_id"]

        if fw_opened := (trigger == prefix+"root-fw-button-search"):  # PARENT trigger
            dr["fw-modal.opened"] = True
            dr["fw-store-context.data"] = "base"
            dr["fw-find-text.value"] = dp["root-store-selected-word.data"]["fwd_word"]
            dr["fw-segmented-within.value"] = "within"
            dr["fw-segmented-lang.value"] = language.title()

            dp["fw-find-text.value"] = dr["fw-find-text.value"]  # needed later

        elif fw_opened := (trigger == prefix+"vl-fw-btn-add-word"):  # PARENT trigger
            dr["fw-modal.opened"] = True
            dr["fw-store-context.data"] = "vocablists"
            dr["vl-modal.opened"] = False

        elif fulltrigger in [prefix+"fw-btn-select.n_clicks", prefix+"fw-aggrid-find.cellDoubleClicked"]:
            context = dp["fw-store-context.data"]
            if dp["fw-aggrid-find.selectedRows"]:
                row = dp['fw-aggrid-find.selectedRows'][0]
                if context == "base":
                    with engine.connect() as conn:
                        sql = f"select * from {table} where fwd_id={row['id']}"
                        df = pd.read_sql(sql, conn)
                    dstore = df.to_dict(orient="records")[0]
                    dr["fw-modal.opened"] = False
                    dr["root-store-selected-word.data"] = dstore
                elif context == "vocablists":
                    new_item = {
                        f"id":row["id"],
                        colheading:row[colheading], 
                        "English word":row["English word"]
                    }
                    dr["fw-modal.opened"] = False
                    dr["vl-aggrid-words.rowData"] = dp["vl-aggrid-words.rowData"]
                    dr["vl-aggrid-words.rowData"].append(new_item)
                else:
                    raise ValueError(f"Unknown context: {context}")

        elif trigger == prefix+"fw-btn-cancel":
            dr["fw-modal.opened"] = False

        # -- populate the table either on window open or user triggers
        if fw_opened or trigger in [prefix+"fw-find-text", prefix+"fw-segmented-within", prefix+"fw-segmented-lang"]:
            dr["fw-aggrid-find.rowData"], \
                dr["fw-text-wordcount.children"] = utils.cre_find_table_data(
                searchstr=dp["fw-find-text.value"],
                engine=engine,
                language=language,
                colheading=colheading,
                searchwithin=(dp["fw-segmented-within.value"] == "within"), 
                searchenglish=(dp["fw-segmented-lang.value"] == "English")
            )

        # -- disable select button if no row selected
        dr["fw-btn-select.disabled"] = (not dp["fw-aggrid-find.selectedRows"])

        # -- may need to re-open parent screen on close
        if (dr["fw-modal.opened"] == False) and (dp["fw-store-context.data"]) == "vocablists":
            dr["vl-modal.opened"] = True

        return utils.cb_results(dr)

# ----------------------------------------------------------------    
# -- There appears no way to set the focus or select text using a normal callback
# -- When modal is opened, set focus to the textinput and select all text
    clientside_callback(
        f"""
        async function(opened) {{
            if (opened) {{
                // Delay 100ms, seems necessary
                await new Promise(r => setTimeout(r, 100));
                let inputid = document.getElementById("{prefix}fw-find-text");
                inputid.focus({{ focusVisible: true }});
                inputid.select();
            }}
            return;
        }}
        """,
        Input(prefix+"fw-modal", "opened"),
    )

