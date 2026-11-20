'''
Callbacks for vocab lists
PARENT OF:
    find word (fw)
    vocab_list_add (fla)
CHILD of:
    main screen (root)
'''
from typing import Any
from dash import Input, Output, State, ctx
import pandas as pd
from sqlalchemy import text
import utils

def cre_callbacks(app, engine, prefix, lspec, adminuser=False):
    language=lspec["language"]
    colheading = lspec["colheading"]

    if not adminuser: # Only set up these if in admin mode
        return

    outputs = [
        ("vl-modal", "opened"), ("vl-select-list", "data"), 
        ("vl-select-list", "value"), ("vl-aggrid-words", "rowData"),
    ]
    inputs = [
        ("root-vl-button-lists","n_clicks"),  # -- PARENT trigger
        ("vl-select-list", "value"), ("vl-btn-cancel","n_clicks"),
        ("vl-btn-ok","n_clicks")
    ]
    states = [
        ("vl-select-list", "value"), ("vl-aggrid-words", "rowData"),
    ]
    callback_outputs = (Output(prefix+elid, elprop, allow_duplicate=True) for (elid, elprop) in outputs)
    callback_inputs = (Input(prefix+elid,elprop) for (elid, elprop) in inputs)
    callback_states = (State(prefix+elid,elprop) for (elid, elprop) in states)
    @app.callback(*callback_outputs, *callback_inputs, *callback_states, prevent_initial_call=True)
    def find_word_callback(*args):
        dp, dr = utils.cb_collate(args, ltrim = len(prefix))
        trigger = ctx.triggered_id
        fulltrigger = ctx.triggered[0]["prop_id"]

        if vl_opened := (trigger == prefix+"root-vl-button-lists"):
            with engine.connect() as conn:
                df = pd.read_sql(
                    f"""select to_char(fwl_id, '99999') value, fwl_name label 
                        from {language}wordlists 
                        order by fwl_name""", 
                    conn
                )
                seldata = df.to_dict(orient="records")

            dr["vl-modal.opened"] = True
            dr["vl-select-list.data"] = seldata
            if seldata:
                dr["vl-select-list.value"] = seldata[0]["value"]
                dp["vl-select-list.value"] =dr["vl-select-list.value"]

        # -- populate the word list if a list is selected
        if (fulltrigger == prefix+"vl-select-list.value") or vl_opened:
            wl_id = int(dp["vl-select-list.value"]) if dp["vl-select-list.value"] else -1
            with engine.connect() as conn:
                df = pd.read_sql(f"""
                                    select fwd_id, fwd_word, fwd_englishword
                                    from {language}words inner join {language}wordinlist
                                    on fwd_id = fwdl_fwd_id 
                                    where fwdl_fwl_id={wl_id}
                                    order by fwd_word
                                """, conn)
                elements = df[[f"fwd_id","fwd_word", f"fwd_englishword"]].\
                    rename(columns={
                        f"fwd_id":"id",
                        "fwd_word":colheading, 
                        f"fwd_englishword":"English word"
                    }).to_dict(orient="records")

            dr["vl-aggrid-words.rowData"] = elements

        if trigger == prefix+"vl-btn-cancel":
            dr["vl-modal.opened"] = False

        if adminuser and trigger == prefix+"vl-btn-ok":
            svalue = dp["vl-select-list.value"]
            agrowdata = dp["vl-aggrid-words.rowData"]

           # Need to retrieve from database and save any changes
            wl_id = int(svalue)
            with engine.connect() as conn:
                df = pd.read_sql(f"""
                                    select fwdl_fwd_id
                                    from {language}wordinlist
                                    where fwdl_fwl_id={wl_id}
                                    order by fwdl_id
                                """, conn)
            
            current = set(df[f"fwdl_fwd_id"])
            new = {d["id"] for d in agrowdata}

            deletions = current - new
            insertions = new - current

            if deletions:
                raise NotImplementedError("Deletions not supported yet")
            
            if insertions:
                with engine.connect() as conn:
                    for id in insertions:
                        sql = f"""insert into {language}wordinlist 
                                (fwdl_fwl_id, fwdl_fwd_id)
                                values ({wl_id}, {id})"""
                        conn.execute(text(sql))
                        x = 0
                    conn.commit()
            dr["vl-modal.opened"] = False            

        return utils.cb_results(dr)
